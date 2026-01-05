from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ProjectEmbedding, ProjectJSON
from .serializers import ProjectEmbeddingInputSerializer, ProjectEmbeddingSerializer, ProjectJSONSerializer
from resumes.models import ResumeEmbedding, ResumeJSON
from external.semantic_project import build_semantic_text_project
from external.embed_project import embed_semantic_text_project
from external.match_users_to_projects import (
	semantic_relevance_filter,
	compute_capability_score,
	compute_trust_score,
	compute_final_score,
	PROJECT_TYPE_ALPHA
)
from ratings.services import get_global_rating_data


@api_view(['POST'])
def generate_project_embedding(request):
	"""
	Generate semantic text and embedding from parsed project JSON.
	
	POST /api/embed/project/
	Body: {
		"project_id": 456,
		"parsed_json": { ... parsed project data from Spring Boot ... }
	}
	
	Returns: {
		"project_id": 456,
		"semantic_text": "...",
		"embedding": [768 floats],
		"created_at": "...",
		"updated_at": "..."
	}
	"""
	input_serializer = ProjectEmbeddingInputSerializer(data=request.data)
	
	if not input_serializer.is_valid():
		return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	project_id = input_serializer.validated_data['project_id']
	parsed_json = input_serializer.validated_data['parsed_json']
	
	try:
		# Store project JSON for later matching (avoid requiring it in match request)
		project_json_record, _ = ProjectJSON.objects.update_or_create(
			project_id=project_id,
			defaults={"project_json": parsed_json}
		)

		# Generate semantic text
		semantic_text = build_semantic_text_project(parsed_json)
		
		# Generate embedding
		embedding = embed_semantic_text_project(semantic_text)
		
		# Store or update
		project_embedding, created = ProjectEmbedding.objects.update_or_create(
			project_id=project_id,
			defaults={
				'semantic_text': semantic_text,
				'embedding': embedding
			}
		)
		
		output_serializer = ProjectEmbeddingSerializer(project_embedding)
		project_json_serializer = ProjectJSONSerializer(project_json_record)
		return Response(
			{
				"message": "Project JSON stored and embedding generated successfully",
				"data": output_serializer.data,
				"project_json": project_json_serializer.data
			},
			status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
		)
		
	except Exception as e:
		return Response(
			{"error": f"Embedding generation failed: {str(e)}"},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR
		)


@api_view(['POST'])
def match_project(request, project_id):
	"""
	Find top-N matching resumes for a project using two-layer scoring.
	
	POST /api/project/match/{project_id}/?top=5
	
	Returns: {
		"project_id": 456,
		"matches": [
			{
				"resume_id": 123,
				"final_score": 0.85,
				"layer1_capability": {
					"capability_score": 0.82,
					"s_semantic": 0.75,
					"s_skills": 0.90,
					"s_experience": 1.0
				},
				"layer2_trust": {
					"trust_score": 0.88,
					"s_rating": 0.85,
					"s_reliability": 0.91,
					"completion_ratio": 0.95
				},
				"scoring_formula": {
					"alpha": 0.65,
					"formula": "..."
				}
			},
			...
		],
		"count": 5
	}
	"""
	try:
		top_n = int(request.query_params.get('top', 5))
	except ValueError:
		top_n = 5
	
	try:
		# Get project embedding
		project_embedding_obj = ProjectEmbedding.objects.get(project_id=project_id)
		proj_emb = project_embedding_obj.embedding
		
		if not proj_emb:
			return Response(
				{"error": f"Project {project_id} has no embedding"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		# Load stored project JSON; allow request body override if provided
		stored_project_json = None
		try:
			stored_project_json = ProjectJSON.objects.get(project_id=project_id).project_json
		except ProjectJSON.DoesNotExist:
			stored_project_json = None
		proj_json = request.data.get('project_json') or stored_project_json or {}

		if not proj_json:
			return Response(
				{"error": "project JSON not found; provide project_json or store it first"},
				status=status.HTTP_400_BAD_REQUEST
			)
		
		project_type = proj_json.get("project_type", "hackathon")
		required_skills = proj_json.get("required_skills", [])
		
		results = []
		total_resumes = ResumeEmbedding.objects.count()
		resumes_with_embeddings = 0
		passed_gate = 0
		
		print(f"\n{'='*60}")
		print(f"[matching] Two-layer matching for project_id={project_id}")
		print(f"[matching] Project type: {project_type}, Skills: {required_skills}")
		print(f"{'='*60}")
		
		# Phase 1: Semantic relevance filter
		phase1_passes = []
		semantic_candidates = []  # keep all with their scores for fallback if gate is too strict
		
		for idx, resume_emb in enumerate(ResumeEmbedding.objects.all(), 1):
			if not resume_emb.embedding:
				print(f"[{idx}/{total_resumes}] resume_id={resume_emb.resume_id}: ❌ No embedding")
				continue
			
			resumes_with_embeddings += 1
			
			# Apply semantic filter
			passes, sem_score, interpretation = semantic_relevance_filter(
				proj_emb, 
				resume_emb.embedding
			)
			
			print(f"[{idx}/{total_resumes}] resume_id={resume_emb.resume_id}: semantic={sem_score:.4f} ({interpretation}), passes={passes}")
			semantic_candidates.append({
				"resume_id": resume_emb.resume_id,
				"embedding": resume_emb.embedding,
				"semantic_score": sem_score,
				"interpretation": interpretation,
				"passed": passes,
			})
			
			if not passes:
				continue
			
			passed_gate += 1
			phase1_passes.append({
				'resume_id': resume_emb.resume_id,
				'embedding': resume_emb.embedding,
				'semantic_score': sem_score
			})
		
		print(f"[matching] Phase 1: {passed_gate}/{resumes_with_embeddings} passed semantic filter")

		# Fallback: if no one passed the semantic gate, take the top-N by semantic score to continue scoring
		if not phase1_passes and semantic_candidates:
			semantic_candidates.sort(key=lambda c: c["semantic_score"], reverse=True)
			top_semantic = semantic_candidates[:top_n]
			phase1_passes = [
				{
					"resume_id": c["resume_id"],
					"embedding": c["embedding"],
					"semantic_score": c["semantic_score"],
				}
				for c in top_semantic
			]
			print(f"[matching] Fallback: semantic gate strict; proceeding with top {len(phase1_passes)} by semantic score")
		
		#we have two phases to compute scores
		#first one is based on the embeddings, gives semantic score

		#second one has two layers capability and alignment, trust and execution
		#-----------------------------------------------------------------------
		
		# Phase 2: Two-layer scoring
		# Fetch stored resume JSONs for candidates we will score
		resume_ids = [candidate['resume_id'] for candidate in phase1_passes]
		stored_resume_jsons = {
			record.resume_id: record.resume_json or {}
			for record in ResumeJSON.objects.filter(resume_id__in=resume_ids)
		}
		# Fallback to request payload if provided (for backward compatibility/tests)
		fallback_resume_jsons = request.data.get('resume_jsons', {})

		#phase1_passes contains resumes that passed the semantic filter

		for candidate in phase1_passes:
			resume_id = candidate['resume_id']
			
			# Get resume JSON from local store, fallback to provided body
			user_json = stored_resume_jsons.get(resume_id) or fallback_resume_jsons.get(str(resume_id), {}) or {}
			
			# Extract data
			profile = user_json.get("profile", {})
			skills = user_json.get("skills", {})
			experience = user_json.get("experience_level", {})
			reputation = user_json.get("reputation_signals", {})
			
			# Layer 1: Capability and Alignment
			capability_data = compute_capability_score(
				proj_emb,
				candidate['embedding'],
				project_type,
				required_skills,
				skills,
				experience.get("overall", "beginner")
			)
			
			# Layer 2: Trust and Execution
			# Fetch ratings and fall back to neutral defaults if unavailable
			global_rating_data = {
				"global_rating": reputation.get("average_rating", 3.5),
				"ratings_count": 0,
			}
			try:
				global_rating_data = get_global_rating_data(int(resume_id))
			except Exception:
				# If ratings service unavailable, use defaults above
				pass
			global_rating = global_rating_data.get("global_rating", reputation.get("average_rating", 3.5))
			completed_projects = reputation.get("completed_projects", 0)
			dropped_projects = 0  # TODO: from project history
			availability = profile.get("availability", "medium")
			
			trust_data = compute_trust_score(
				global_rating,
				completed_projects,
				dropped_projects,
				availability
			)
			
			# Final score
			final_score_data = compute_final_score(
				capability_data["capability_score"],
				trust_data["trust_score"],
				project_type
			)
			
			print(f"    └─ resume_id={resume_id}: Final={final_score_data['final_score']:.4f} (C={capability_data['capability_score']:.4f}, T={trust_data['trust_score']:.4f})")
			
			results.append({
				"resume_id": resume_id,
				"final_score": final_score_data["final_score"],
				"layer1_capability": capability_data,
				"layer2_trust": trust_data,
				"scoring_formula": final_score_data,
				"ratings": global_rating_data,
				"profile": {
					"name": profile.get("name", "Unknown"),
					"year": profile.get("year", "Unknown"),
					"availability": availability
				}
			})
		
		# Sort by final score
		results.sort(key=lambda r: r["final_score"], reverse=True)
		
		print(f"\n{'='*60}")
		print(f"[matching] Summary:")
		print(f"  Total resumes: {total_resumes}")
		print(f"  With embeddings: {resumes_with_embeddings}")
		print(f"  Passed semantic gate: {passed_gate}")
		print(f"  Final matches: {len(results)}")
		print(f"{'='*60}\n")
		
		return Response({
			"project_id": project_id,
			"project_type": project_type,
			"alpha": PROJECT_TYPE_ALPHA.get(project_type, 0.65),
			"matches": results,  # Return all matches, not limited to top_n
			"count": len(results),
			"top_n_requested": top_n,  # Include what was requested
			"project_metadata": {
				"title": proj_json.get("title"),
				"description": proj_json.get("description"),
				"required_skills": proj_json.get("required_skills", []),
				"preferred_technologies": proj_json.get("preferred_technologies", []),
				"domains": proj_json.get("domains", []),
				"project_type": proj_json.get("project_type"),
			},
			"stats": {
				"total_resumes": total_resumes,
				"with_embeddings": resumes_with_embeddings,
				"passed_filter": passed_gate
			}
		}, status=status.HTTP_200_OK)
		
	except ProjectEmbedding.DoesNotExist:
		return Response(
			{"error": f"Project {project_id} not found or has no embedding"},
			status=status.HTTP_404_NOT_FOUND
		)
	except Exception as e:
		import traceback
		print(traceback.format_exc())
		return Response(
			{"error": f"Matching failed: {str(e)}"},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR
		)


