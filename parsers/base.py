import hashlib
import os

class BaseSaveParser:
    """
    Classe base para todos os parsers de Save.
    Qualquer geração adicionada no futuro deve estender esta classe
    e implementar o método `extract_pokemon`.
    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.file_data = self._read_file()
        self.file_hash = self._generate_hash()

    def _read_file(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.filepath}")
        with open(self.filepath, 'rb') as f:
            return f.read()

    def _generate_hash(self):
        return hashlib.sha256(self.file_data).hexdigest()

    def extract_pokemon(self):
        """
        Deve ser sobrescrito por cada classe filha.
        Retorna uma lista de dicionários contendo os dados dos Pokémon extraídos,
        prontos para serem mapeados para o modelo PokemonInstance.
        """
        raise NotImplementedError("O método extract_pokemon deve ser implementado nas classes filhas.")