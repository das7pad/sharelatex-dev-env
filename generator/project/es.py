from generator.project import Project


class ESProject(Project):
    language = 'es'

    def _get_files_to_update(
        self,
    ):
        return super()._get_files_to_update() + [
            '.nvmrc',
            'Dockerfile',
        ]
