import csv, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"tools"))
from localization_common import controls, display_lines, immutable_tokens, visible_text
from validate_dialogues import measured_lines, validate
from validate_terminology import load_canonical, validate_assignments, validate_prose
from generate_patch import number

class ControlsTest(unittest.TestCase):
    def test_control_does_not_swallow_visible_tail(self):
        text=r"Avant\c\h08ó\when I stood"
        self.assertEqual([x.value for x in controls(text)],[r"\c",r"\h08",r"\w"])
        self.assertEqual(visible_text(text,keep_layout=False),"Avantóhen I stood")

    def test_immutable_order_and_parameters(self):
        source=r"[player]\c\h08 texte [buffer1]"
        self.assertNotEqual(immutable_tokens(source),immutable_tokens(r"[player]\c\h09 texte [buffer1]"))
        self.assertNotEqual(immutable_tokens(source),immutable_tokens(r"[buffer1]\c\h08 texte [player]"))

    def test_layout_may_change_but_must_be_valid(self):
        self.assertEqual(immutable_tokens(r"A\nB\pC"),immutable_tokens(r"A B\nC"))
        with self.assertRaises(ValueError): display_lines(r"A\nB\nC")
        with self.assertRaises(ValueError): display_lines(r"A\lB")

    def test_character_validation_keeps_tail(self):
        self.assertIn("INTERDIT",visible_text(r"A\c\h08INTERDIT",keep_layout=False))

class CatalogueTest(unittest.TestCase):
    def test_missing_extra_and_duplicate_ids_rejected(self):
        original=ROOT/"translation/dialogues_fr.csv"
        with original.open(encoding="utf-8",newline="") as handle:
            rows=list(csv.DictReader(handle))
        fields=rows[0].keys()
        rows=rows[1:]+[dict(rows[1]),dict(rows[1])]; rows[-1]["id"]="foreign"
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bad.csv"
            with path.open("w",encoding="utf-8",newline="") as h:
                writer=csv.DictWriter(h,fields);writer.writeheader();writer.writerows(rows)
            *_,issues=validate(path,ROOT)
        messages=" ".join(x[2] for x in issues)
        self.assertIn("absent du catalogue",messages); self.assertIn("étranger au catalogue",messages); self.assertIn("présent 2 fois",messages)

class CanonicalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=load_canonical(ROOT/"translation/canonical/canonical_fr_gen3.csv")
    def test_required_canonical_terms(self):
        expected={"MOVE_THUNDER":"Fatal-Foudre","MOVE_THUNDERBOLT":"Tonnerre","MOVE_THUNDER_SHOCK":"Éclair","MOVE_THUNDER_WAVE":"Cage-Éclair","SPECIES_BULBASAUR":"Bulbizarre","SPECIES_CHARIZARD":"Dracaufeu","SPECIES_SQUIRTLE":"Carapuce"}
        self.assertEqual({k:self.data[k]["french_canonical"] for k in expected},expected)
    def test_invented_thunder_is_rejected(self):
        issues=validate_assignments([{"internal_id":"MOVE_THUNDER","french":"Éclair Assassin"}],self.data)
        self.assertEqual(issues[0][0],"ERROR")
    def test_english_species_and_unambiguous_move_are_errors(self):
        species=validate_prose("Charizard",self.data)
        move=validate_prose("Thunder Wave",self.data)
        self.assertEqual(species[0][0],"ERROR")
        self.assertEqual(move[0][0],"ERROR")

class PlaceholderWidthTest(unittest.TestCase):
    def test_player_placeholder_reserves_seven_widest_glyphs(self):
        literal="W"*24  # 192px before the substituted player name
        _,_,pixels,_=measured_lines(literal+"[player]")[0]
        self.assertEqual(pixels,248)
        self.assertGreater(pixels,198)
    def test_unknown_buffer_is_never_zero_width(self):
        _,_,pixels,unknown=measured_lines("W"*12+"[buffer1]")[0]
        self.assertEqual(pixels,192)
        self.assertEqual(unknown,["[buffer1]"])

class StatusTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/"translation/dialogues_fr.csv").open(encoding="utf-8",newline="") as h:
            cls.rows=list(csv.DictReader(h)); cls.fields=cls.rows[0].keys()
        cls.index=next(i for i,row in enumerate(cls.rows) if not immutable_tokens(row["source"]))
    def run_changed(self,fr,status):
        rows=[dict(row) for row in self.rows]; rows[self.index]["fr"]=fr; rows[self.index]["status"]=status
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"catalogue.csv"
            with path.open("w",encoding="utf-8",newline="") as h:
                writer=csv.DictWriter(h,self.fields); writer.writeheader(); writer.writerows(rows)
            *_,issues=validate(path,ROOT)
        return [issue for issue in issues if issue[1]==rows[self.index]["id"]]
    def test_empty_validated_is_error(self): self.assertTrue(any(x[0]=="ERREUR" for x in self.run_changed("","validé")))
    def test_empty_translated_is_error(self): self.assertTrue(any(x[0]=="ERREUR" for x in self.run_changed("","traduit")))
    def test_valid_translation_and_status_are_ok(self): self.assertEqual(self.run_changed("Bonjour.","traduit"),[])
    def test_unknown_status_is_error(self): self.assertTrue(any(x[0]=="ERREUR" for x in self.run_changed("Bonjour.","terminé")))
    def test_dialogue_qa_rejects_charizard(self):
        self.assertTrue(any("SPECIES_CHARIZARD" in x[2] and x[0]=="ERREUR" for x in self.run_changed("Charizard","traduit")))
    def test_dialogue_qa_rejects_thunder_wave(self):
        self.assertTrue(any("MOVE_THUNDER_WAVE" in x[2] and x[0]=="ERREUR" for x in self.run_changed("Thunder Wave","traduit")))

class PatchTest(unittest.TestCase):
    def test_bps_variable_length_integer_has_final_bit(self):
        self.assertEqual(number(0),b"\x80")
        self.assertEqual(number(127),b"\xff")
        self.assertEqual(number(128),b"\x00\x80")

if __name__=="__main__": unittest.main()
