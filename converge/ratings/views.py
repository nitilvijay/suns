from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import SubmitRatingSerializer, RatingSerializer
from .services import submit_rating_record, get_global_rating_data


@api_view(['POST', 'OPTIONS'])
def submit_rating(request):
	"""Submit a peer rating after project completion."""
	if request.method == 'OPTIONS':
		return Response(status=status.HTTP_200_OK)
	try:
		print(f"[ratings] Raw request data: {request.data}")
		serializer = SubmitRatingSerializer(data=request.data)
		if not serializer.is_valid():
			print(f"[ratings] Validation errors: {serializer.errors}")
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		data = serializer.validated_data
		print(f"[ratings] Validated data: rater={data['rater_id']}, ratee={data['ratee_id']}, project={data['project_id']}")
		record = submit_rating_record(
			rater_id=data['rater_id'],
			ratee_id=data['ratee_id'],
			project_id=data['project_id'],
			category_scores=data['category_scores']
		)
		print(f"[ratings] Rating stored successfully: {record}")
		return Response(RatingSerializer(record).data, status=status.HTTP_201_CREATED)
	except Exception as e:
		import traceback
		print(f"[ratings] Exception: {e}")
		print(traceback.format_exc())
		return Response(
			{"error": str(e)},
			status=status.HTTP_500_INTERNAL_SERVER_ERROR
		)


@api_view(['GET', 'OPTIONS'])
def user_rating(request, ratee_id):
	"""Get global rating for a user (Bayesian smoothed)."""
	if request.method == 'OPTIONS':
		return Response(status=status.HTTP_200_OK)
	data = get_global_rating_data(ratee_id)
	return Response(data, status=status.HTTP_200_OK)
