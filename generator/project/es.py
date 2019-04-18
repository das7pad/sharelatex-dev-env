from generator.project import Project


class ESProject(Project):
    language = 'es'

    def _update_nvmrc(self):
        nvm_rc = self._path / '.nvmrc'

        current_node_version = nvm_rc.read_text().strip()
        new_node_version = self['node_version']

        if current_node_version == new_node_version:
            return False

        self._changed = True
        nvm_rc.write_text(new_node_version + '\n')
        return True

    def process(
        self,
        **kwargs
    ):
        self._update_nvmrc()

        return super().process(**kwargs)
