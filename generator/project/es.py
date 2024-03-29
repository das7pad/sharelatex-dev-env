from generator.project import Project


class ESProject(Project):
    language = 'es'

    @classmethod
    def _get_deleted_templates(cls):
        return super()._get_deleted_templates().union(
            {
                'docker-compose-config.yml',
            }
        )

    def _get_src_dir(self):
        return self['src_dir'] if 'src_dir' in self else 'js'

    def _get_env(self):
        env = super()._get_env()
        env['src_dir'] = self._get_src_dir()
        return env

    def _get_cfg_fields(
        self,
    ):
        return [
            'language',
            'src_dir',
            'node_version',
            'dependencies',
            'docker_repos',
            'kube',
            'build_target',
            self.insert_marker,
        ]

    def _get_possible_project_files(
        self,
    ):
        src_dir = self._get_src_dir()
        files = super()._get_possible_project_files()
        files.update({
            'has_app_js': 'app.js',
            'has_app_src': 'app/%s' % src_dir,
            'has_acceptance_test_bootstrap': 'test/acceptance/bootstrap.js',
            'has_acceptance_test_config_js':
                'test/acceptance/config/settings.test.js',
            'has_acceptance_test_init': 'test/acceptance/%s/Init.js' % src_dir,
            'has_babel_config_json': 'babel.config.json',
            'has_esbuild_js': 'esbuild.js',
            'has_frontend_test_bootstrap': 'test/frontend/bootstrap.js',
            'has_index_js': 'index.js',
            'has_locales': 'locales/',
            'has_populatePublicVendor_js': 'populatePublicVendor.js',
            'has_postcss_config_js': 'postcss.config.js',
            'has_unit_test_bootstrap': 'test/unit/bootstrap.js',
        })
        return files
