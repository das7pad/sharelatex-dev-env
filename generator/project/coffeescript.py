from generator.project.es import ESProject


class CoffeeScriptProject(ESProject):
    language = 'coffeescript'

    def _get_possible_project_files(
        self,
    ):
        files = super()._get_possible_project_files()
        files.update({
            'has_acceptance_test_init': 'test/acceptance/coffee/Init.coffee',
        })
        return files
