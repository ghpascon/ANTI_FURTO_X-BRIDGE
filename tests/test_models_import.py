from app.models import get_all_models


def test_import_tag_event_models():
	models = get_all_models()
	model_names = [model.__name__ for model in models]
	assert 'Tag' in model_names
	assert 'Event' in model_names
