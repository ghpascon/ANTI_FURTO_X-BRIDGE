from app.core.build_templates import TemplateManager
import os


def test_template_manager_init():
	templates_dir = os.path.join(os.path.dirname(__file__), '../app/templates')
	os.makedirs(templates_dir, exist_ok=True)
	tm = TemplateManager(templates_dir)
	assert tm.templates is not None
	assert hasattr(tm.templates, 'env')
