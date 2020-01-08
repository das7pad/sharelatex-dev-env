from generator.project.es import ESProject


class CoffeeScriptProject(ESProject):
    language = 'coffeescript'

    def _get_possible_project_files(
        self,
    ):
        files = super()._get_possible_project_files()
        files.update({
            'has_app_js': 'app.coffee',
            'has_app_src': 'app/coffee',
            'has_acceptance_test_bootstrap': 'test/acceptance/bootstrap.coffee',
            'has_acceptance_test_init': 'test/acceptance/coffee/Init.coffee',
            'has_index_js': 'index.coffee',
            'has_unit_test_bootstrap': 'test/unit/bootstrap.coffee',
        })
        return files
