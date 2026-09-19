import struct
from .base import BaseSaveParser


class Gen3SaveParser(BaseSaveParser):
    """Parser para saves de Pokemon Emerald / Gen III.

    Esta implementacao trabalha com a estrutura real do save:
    - 2 slots de 14 setores de 0x1000 bytes;
    - setores identificados pelo Section ID, pois a ordem fisica gira a cada save;
    - SaveBlock1 nos setores 1-4;
    - PokemonStorage nos setores 5-13;
    - Party dentro do SaveBlock1;
    - BoxPokemon de 80 bytes e Pokemon de Party de 100 bytes;
    - descriptografia por PID ^ OT ID;
    - checksum dos 48 bytes seguros;
    - tabela de caracteres Gen III para nickname/OT;
    - level exato da Party e level do PC calculado pela curva de EXP da especie.

    Observacao importante:
    `species_id` retornado pela classe e o National Dex number (1-386),
    porque isso normalmente corresponde ao ID usado pela tabela Species da
    aplicacao. O ID interno da Gen III fica em `internal_species_id`.
    """

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    SECTOR_SIZE = 0x1000
    SECTOR_DATA_SIZE = 0xF80
    SECTORS_PER_SLOT = 14
    SAVE_SLOT_SIZE = SECTOR_SIZE * SECTORS_PER_SLOT
    SAVE_SIZE = SAVE_SLOT_SIZE * 2

    SIGNATURE = 0x08012025
    SECTION_ID_OFFSET = 0xFF4
    CHECKSUM_OFFSET = 0xFF6
    SIGNATURE_OFFSET = 0xFF8
    SAVE_COUNTER_OFFSET = 0xFFC

    # SaveBlock1 = setores 1..4
    SAVEBLOCK1_START = 1
    SAVEBLOCK1_END = 4

    # PokemonStorage = setores 5..13
    PC_START_ID = 5
    PC_END_ID = 13

    # Party dentro do SaveBlock1.
    # PARTY_COUNT ocupa 4 bytes em 0x234 e os Pokemon iniciam em 0x238.
    PARTY_COUNT_OFFSET = 0x234
    PARTY_OFFSET = 0x238

    BOX_COUNT = 14
    POKEMON_PER_BOX = 30
    BOX_POKEMON_SIZE = 80
    PARTY_POKEMON_SIZE = 100

    # Gen III Emerald possui especies internas ate Chimecho = 411.
    # 412 e o slot interno de Egg.
    MAX_INTERNAL_SPECIES = 411
    EGG_INTERNAL_SPECIES = 412

    # ------------------------------------------------------------------
    # Pokemon
    # ------------------------------------------------------------------
    SUBSTRUCTURE_ORDER = [
        "GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA",
        "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
        "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG",
        "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG",
    ]

    # ------------------------------------------------------------------
    # Curvas de EXP da Gen III.
    # Os IDs aqui sao National Dex IDs.
    # ------------------------------------------------------------------
    _GROWTH_MEDIUM_SLOW = set()
    _GROWTH_MEDIUM_FAST = set()
    _GROWTH_FAST = set()
    _GROWTH_SLOW = set()
    _GROWTH_ERRATIC = set()
    _GROWTH_FLUCTUATING = set()

    @classmethod
    def _build_growth_groups(cls):
        """Monta as tabelas de crescimento usadas por Emerald."""
        if cls._GROWTH_MEDIUM_SLOW:
            return

        def add(group, *parts):
            for part in parts:
                if isinstance(part, tuple):
                    group.update(range(part[0], part[1] + 1))
                else:
                    group.add(part)

        # Medium Slow
        add(cls._GROWTH_MEDIUM_SLOW,
            (1, 9), (16, 18), (29, 34), (43, 45), (60, 71),
            (74, 76), (92, 94), (151, 160), (179, 182), (186, 189),
            (191, 192), 198, 207, 213, 215, (251, 260), (270, 277),
            (293, 295), 302, (315, 315), (328, 332), 352, 359,
            (363, 365))

        # Medium Fast
        add(cls._GROWTH_MEDIUM_FAST,
            (10, 15), (19, 28), (37, 38), (41, 42), (46, 57),
            (77, 89), (95, 101), (104, 110), (114, 119), (122, 126),
            (132, 141), (161, 164), 169, 172, (177, 178), 185,
            (193, 197), 199, (201, 206), 208, (211, 212), (216, 219),
            (223, 224), (230, 233), (236, 240), (261, 269), (278, 279),
            (283, 284), 299, (307, 308), (311, 312), (322, 324),
            (339, 340), (343, 344), 351, (360, 362))

        # Fast
        add(cls._GROWTH_FAST,
            (35, 36), 113, (39, 40), (165, 168), (173, 176), (183, 184),
            190, 200, (209, 210), 222, 225, 235, 242, 298, (300, 301),
            (303, 303), (325, 327), (337, 338), (353, 356), 358, 370)

        # Slow
        add(cls._GROWTH_SLOW,
            (58, 59), (72, 73), (90, 91), (102, 103), (111, 112),
            (120, 121), (127, 131), (142, 150), (170, 171), 214,
            (220, 221), (226, 229), 234, (241, 241), (243, 250),
            (280, 282), (287, 289), (304, 306), (309, 310), (318, 319),
            357, 369, (371, 386))

        # Erratic
        add(cls._GROWTH_ERRATIC,
            (290, 292), 313, (333, 335), (345, 350), (366, 368))

        # Fluctuating
        add(cls._GROWTH_FLUCTUATING,
            (285, 286), (296, 297), 314, (316, 317), (320, 321), 336,
            (341, 342))

    # ------------------------------------------------------------------
    # Gen III text
    # ------------------------------------------------------------------
    _SPECIAL_CHARS = {
        0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç",
        0x05: "È", 0x06: "É", 0x07: "Ê", 0x08: "Ë",
        0x09: "Ì", 0x0B: "Î", 0x0C: "Ï", 0x0D: "Ò",
        0x0E: "Ó", 0x0F: "Ô", 0x10: "Œ", 0x11: "Ù",
        0x12: "Ú", 0x13: "Û", 0x14: "Ñ", 0x15: "ß",
        0x16: "à", 0x17: "á", 0x19: "ç", 0x1A: "è",
        0x1B: "é", 0x1C: "ê", 0x1D: "ë", 0x1E: "ì",
        0x20: "î", 0x21: "ï", 0x22: "ò", 0x23: "ó",
        0x24: "ô", 0x25: "œ", 0x26: "ù", 0x27: "ú",
        0x28: "û", 0x29: "ñ", 0x2A: "º", 0x2B: "ª",
    }

    _PUNCTUATION = {
        0x2E: "&", 0x2F: "+", 0x51: "¿", 0x52: "¡",
        0x5B: "%", 0x5C: "(", 0x5D: ")",
        0xA0: "ʳᵉ", 0xAB: "!", 0xAC: "?", 0xAD: ".",
        0xAE: "-", 0xAF: "・", 0xB0: "…", 0xB1: "“",
        0xB2: "”", 0xB3: "‘", 0xB4: "’", 0xB5: "♂",
        0xB6: "♀", 0xB7: "₽", 0xB8: ",", 0xB9: "×",
        0xBA: "/", 0xEF: "▶", 0xF0: ":", 0xF1: "Ä",
        0xF2: "Ö", 0xF3: "Ü", 0xF4: "ä", 0xF5: "ö",
        0xF6: "ü",
    }

    def __init__(self, filepath):
        super().__init__(filepath)
        self._build_growth_groups()

    # ==================================================================
    # Entrada principal
    # ==================================================================
    def extract_pokemon(self):
        if len(self.file_data) < self.SAVE_SIZE:
            raise ValueError(
                f"Save Gen 3 incompleto: {len(self.file_data)} bytes. "
                f"Esperado pelo menos {self.SAVE_SIZE} bytes."
            )

        slots = self._read_save_slots()
        valid_slots = [slot for slot in slots if slot["valid"]]

        if not valid_slots:
            raise ValueError(
                "Nenhum dos dois slots de save foi validado. "
                "O arquivo pode nao ser um save original de Pokemon Emerald "
                "ou pode estar corrompido."
            )

        selected = self._select_latest_slot(valid_slots)
        sections = selected["sections"]

        print(
            f"Save Gen 3 valido: slot fisico {selected['slot'] + 1}, "
            f"counter={selected['counter']}"
        )

        save_block1 = self._assemble_sections(
            sections,
            self.SAVEBLOCK1_START,
            self.SAVEBLOCK1_END,
        )
        pc_storage = self._assemble_sections(
            sections,
            self.PC_START_ID,
            self.PC_END_ID,
        )

        party = self._extract_party(save_block1)
        pc = self._extract_pc(pc_storage)

        all_pokemon = party + pc

        print(
            f"Pokemon validos encontrados: {len(all_pokemon)} "
            f"({len(party)} Party + {len(pc)} PC)"
        )

        return all_pokemon

    # ==================================================================
    # Save sectors
    # ==================================================================
    def _read_save_slots(self):
        slots = []

        for slot_index in range(2):
            base = slot_index * self.SAVE_SLOT_SIZE
            sections = {}
            physical = []

            for physical_sector in range(self.SECTORS_PER_SLOT):
                offset = base + physical_sector * self.SECTOR_SIZE
                sector = self.file_data[offset:offset + self.SECTOR_SIZE]

                if len(sector) != self.SECTOR_SIZE:
                    continue

                section_id = struct.unpack_from(
                    "<H", sector, self.SECTION_ID_OFFSET
                )[0]
                stored_checksum = struct.unpack_from(
                    "<H", sector, self.CHECKSUM_OFFSET
                )[0]
                signature = struct.unpack_from(
                    "<I", sector, self.SIGNATURE_OFFSET
                )[0]
                counter = struct.unpack_from(
                    "<I", sector, self.SAVE_COUNTER_OFFSET
                )[0]

                if signature != self.SIGNATURE:
                    continue

                if section_id >= self.SECTORS_PER_SLOT:
                    continue

                data = sector[:self.SECTOR_DATA_SIZE]
                calculated_checksum = self._calculate_sector_checksum(data)

                if calculated_checksum != stored_checksum:
                    continue

                # Section IDs precisam ser unicos dentro do slot.
                if section_id in sections:
                    continue

                sections[section_id] = {
                    "data": data,
                    "counter": counter,
                    "physical_sector": physical_sector,
                    "file_offset": offset,
                }
                physical.append(sections[section_id])

            counters = {item["counter"] for item in physical}
            counters_match = len(counters) == 1
            complete = len(sections) == self.SECTORS_PER_SLOT

            slot_counter = next(iter(counters)) if counters_match else None

            slots.append({
                "slot": slot_index,
                "sections": sections,
                "counter": slot_counter,
                "valid": complete and counters_match,
            })

        return slots

    @staticmethod
    def _calculate_sector_checksum(data):
        """Checksum usado pelo save Gen 3: soma de palavras u32."""
        checksum = 0
        usable = len(data) - (len(data) % 4)

        for offset in range(0, usable, 4):
            checksum = (checksum + struct.unpack_from("<I", data, offset)[0]) & 0xFFFFFFFF

        return ((checksum >> 16) + (checksum & 0xFFFF)) & 0xFFFF

    @staticmethod
    def _counter_is_newer(a, b):
        """Compara contadores unsigned de 32 bits, tratando overflow."""
        if a == b:
            return False
        return ((a - b) & 0xFFFFFFFF) < 0x80000000

    def _select_latest_slot(self, slots):
        latest = slots[0]

        for slot in slots[1:]:
            if self._counter_is_newer(slot["counter"], latest["counter"]):
                latest = slot

        return latest

    def _assemble_sections(self, sections, first_id, last_id):
        result = bytearray()

        for section_id in range(first_id, last_id + 1):
            section = sections.get(section_id)
            if section is None:
                raise ValueError(
                    f"Setor {section_id} ausente no slot de save selecionado."
                )
            result.extend(section["data"])

        return bytes(result)

    # ==================================================================
    # Party
    # ==================================================================
    def _extract_party(self, save_block1):
        party = []

        if len(save_block1) < self.PARTY_OFFSET:
            return party

        party_count = struct.unpack_from(
            "<I", save_block1, self.PARTY_COUNT_OFFSET
        )[0]

        if party_count > 6:
            print(f"Party count invalido ({party_count}); limitando a 6.")
            party_count = 6

        for slot in range(party_count):
            offset = self.PARTY_OFFSET + slot * self.PARTY_POKEMON_SIZE
            end = offset + self.PARTY_POKEMON_SIZE

            if end > len(save_block1):
                break

            block = save_block1[offset:end]
            pokemon = self._parse_pokemon(block[:self.BOX_POKEMON_SIZE])

            if not pokemon:
                continue

            # O level da Party ja esta armazenado no objeto Pokemon.
            # Offset 0x54 = level.
            cached_level = block[0x54]
            if 1 <= cached_level <= 100:
                pokemon["level"] = cached_level

            pokemon["box"] = 0
            pokemon["slot"] = slot + 1
            pokemon["storage"] = "party"

            party.append(pokemon)

        return party

    # ==================================================================
    # PC
    # ==================================================================
    def _extract_pc(self, pc_storage):
        pokemon_list = []

        # PokemonStorage:
        # 0x0000 currentBox (u8)
        # 0x0004 boxes[14][30]
        pokemon_start = 0x0004

        total = self.BOX_COUNT * self.POKEMON_PER_BOX

        for index in range(total):
            offset = pokemon_start + index * self.BOX_POKEMON_SIZE
            end = offset + self.BOX_POKEMON_SIZE

            if end > len(pc_storage):
                break

            block = pc_storage[offset:end]
            pokemon = self._parse_pokemon(block)

            if not pokemon:
                continue

            box = index // self.POKEMON_PER_BOX + 1
            slot = index % self.POKEMON_PER_BOX + 1

            pokemon["box"] = box
            pokemon["slot"] = slot
            pokemon["storage"] = "pc"

            pokemon_list.append(pokemon)

        return pokemon_list

    # ==================================================================
    # Pokemon
    # ==================================================================
    def _parse_pokemon(self, block):
        if len(block) != self.BOX_POKEMON_SIZE:
            return None

        pid = struct.unpack_from("<I", block, 0x00)[0]
        ot_id_full = struct.unpack_from("<I", block, 0x04)[0]

        # Slot vazio.
        if pid == 0 or pid == 0xFFFFFFFF:
            return None

        if ot_id_full == 0xFFFFFFFF:
            return None

        # Header do BoxPokemon.
        nickname_bytes = block[0x08:0x12]
        language = block[0x12]
        flags = block[0x13]
        ot_name_bytes = block[0x14:0x1B]
        stored_checksum = struct.unpack_from("<H", block, 0x1C)[0]

        is_bad_egg = bool(flags & 0x01)
        has_species = bool(flags & 0x02)
        is_egg = bool(flags & 0x04)

        if is_bad_egg:
            return None

        if not has_species:
            return None

        # Os 48 bytes seguros estao em 0x20..0x4F.
        encrypted = block[0x20:0x50]
        key = pid ^ ot_id_full

        decrypted = bytearray(48)
        for offset in range(0, 48, 4):
            value = struct.unpack_from("<I", encrypted, offset)[0]
            value ^= key
            struct.pack_into("<I", decrypted, offset, value)

        # Checksum oficial do BoxPokemon.
        calculated_checksum = self._calculate_pokemon_checksum(decrypted)
        if calculated_checksum != stored_checksum:
            return None

        order = self.SUBSTRUCTURE_ORDER[pid % 24]
        growth_index = order.index("G") * 12

        internal_species = struct.unpack_from(
            "<H", decrypted, growth_index + 0x00
        )[0]

        if internal_species == self.EGG_INTERNAL_SPECIES:
            # Eggs nao sao especies para o Living Dex.
            return None

        if internal_species <= 0 or internal_species > self.MAX_INTERNAL_SPECIES:
            return None

        national_dex = self._internal_to_national(internal_species)
        if national_dex is None or not (1 <= national_dex <= 386):
            return None

        experience = struct.unpack_from(
            "<I", decrypted, growth_index + 0x04
        )[0]

        ot_id = ot_id_full & 0xFFFF
        secret_id = (ot_id_full >> 16) & 0xFFFF
        pid_high = (pid >> 16) & 0xFFFF
        pid_low = pid & 0xFFFF

        shiny_value = ot_id ^ secret_id ^ pid_high ^ pid_low
        is_shiny = shiny_value < 8

        nickname = self._decode_gen3_string(nickname_bytes)
        ot_name = self._decode_gen3_string(ot_name_bytes)

        level = self._level_from_exp(national_dex, experience)

        return {
            # species_id e mantido como National Dex para encaixar na tabela
            # Species usada pelo saves.py.
            "species_id": national_dex,
            "internal_species_id": internal_species,
            "national_dex_number": national_dex,
            "pid": pid,
            "ot_id": ot_id,
            "secret_id": secret_id,
            "nickname": nickname,
            "ot_name": ot_name,
            "language": language,
            "is_shiny": is_shiny,
            "is_egg": is_egg,
            "experience": experience,
            "level": level,
        }

    @staticmethod
    def _calculate_pokemon_checksum(decrypted):
        checksum = 0
        for offset in range(0, 48, 2):
            checksum = (
                checksum + struct.unpack_from("<H", decrypted, offset)[0]
            ) & 0xFFFF
        return checksum

    @staticmethod
    def _internal_to_national(internal_species):
        # Emerald:
        # 1..251 = Kanto/Johto na mesma numeracao nacional.
        # 252..276 = formas internas antigas de Unown -> National #201.
        # 277..411 = Hoenn #252..386.
        if 1 <= internal_species <= 251:
            return internal_species

        if 252 <= internal_species <= 276:
            return 201

        if 277 <= internal_species <= 411:
            return internal_species - 25

        return None

    # ==================================================================
    # Text decoder
    # ==================================================================
    def _decode_gen3_byte(self, value):
        if value == 0x00:
            return " "

        # Terminador de texto Gen III.
        if value == 0xFF:
            return None

        if 0xBB <= value <= 0xD4:
            return chr(ord("A") + (value - 0xBB))

        if 0xD5 <= value <= 0xEE:
            return chr(ord("a") + (value - 0xD5))

        if 0xA1 <= value <= 0xAA:
            return chr(ord("0") + (value - 0xA1))

        if value in self._SPECIAL_CHARS:
            return self._SPECIAL_CHARS[value]

        if value in self._PUNCTUATION:
            return self._PUNCTUATION[value]

        # Alguns saves/versoes usam 0xF1..0xF6 para acentos maiusculos.
        return ""

    def _decode_gen3_string(self, data):
        chars = []

        for value in data:
            if value == 0xFF:
                break

            char = self._decode_gen3_byte(value)
            if char is None:
                break

            chars.append(char)

        result = "".join(chars).rstrip(" ")
        return result if result else None

    # ==================================================================
    # EXP -> Level
    # ==================================================================
    def _growth_rate_for_national(self, national_dex):
        if national_dex in self._GROWTH_MEDIUM_SLOW:
            return "medium_slow"
        if national_dex in self._GROWTH_MEDIUM_FAST:
            return "medium_fast"
        if national_dex in self._GROWTH_FAST:
            return "fast"
        if national_dex in self._GROWTH_SLOW:
            return "slow"
        if national_dex in self._GROWTH_ERRATIC:
            return "erratic"
        if national_dex in self._GROWTH_FLUCTUATING:
            return "fluctuating"

        # Nunca deveria ocorrer para 1..386; mantemos Medium Fast como
        # fallback para evitar quebrar a importacao caso uma tabela seja
        # expandida futuramente.
        return "medium_fast"

    @staticmethod
    def _exp_for_level(level, growth_rate):
        n = level

        if n <= 1:
            return 0

        if growth_rate == "medium_fast":
            return n ** 3

        if growth_rate == "medium_slow":
            return (6 * n ** 3) // 5 - 15 * n ** 2 + 100 * n - 140

        if growth_rate == "fast":
            return (4 * n ** 3) // 5

        if growth_rate == "slow":
            return (5 * n ** 3) // 4

        if growth_rate == "erratic":
            if n <= 50:
                return (n ** 3 * (100 - n)) // 50
            if n <= 68:
                return (n ** 3 * (150 - n)) // 100
            if n <= 98:
                return (n ** 3 * ((1911 - 10 * n) // 3)) // 500
            return (n ** 3 * (160 - n)) // 100

        if growth_rate == "fluctuating":
            if n <= 15:
                return (n ** 3 * (((n + 1) // 3) + 24)) // 50
            if n <= 36:
                return (n ** 3 * (n + 14)) // 50
            return (n ** 3 * ((n // 2) + 32)) // 50

        return n ** 3

    def _level_from_exp(self, national_dex, experience):
        if experience <= 0:
            return 1

        growth_rate = self._growth_rate_for_national(national_dex)

        # Busca binaria entre 1 e 100.
        low = 1
        high = 100

        while low < high:
            mid = (low + high + 1) // 2
            required = self._exp_for_level(mid, growth_rate)

            if required <= experience:
                low = mid
            else:
                high = mid - 1

        return max(1, min(100, low))

    # ------------------------------------------------------------------
    # Compatibilidade com codigo antigo
    # ------------------------------------------------------------------
    def _get_test_pokemon(self):
        """Mantido apenas para compatibilidade com versoes antigas."""
        return []