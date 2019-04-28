from generator.project import Project


class ESProject(Project):
    language = 'es'

    def _get_cfg_fields(
        self,
    ):
        return [
            'language',
            'node_version',
            'acceptance_creds',
            'dependencies',
            'docker_repos',
            'kube',
            'build_target',
            self.insert_marker,
            'script_version',
        ]
