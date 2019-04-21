from generator.project import Project


class ESProject(Project):
    language = 'es'

    def _get_files_to_update(
        self,
    ):
        files = super()._get_files_to_update() + [
            '.nvmrc',
            'Dockerfile',
            'docker-compose.yml',
            'docker-compose.ci.yml',
            'Jenkinsfile',
            'Jenkinsfile.ce',
            'Makefile',
        ]

        if 'script_version' in self._kwargs:
            version = self._kwargs['script_version']
            if version == '1.1.11':
                files.append(
                    'docker-compose-config.yml'
                )

        return files
