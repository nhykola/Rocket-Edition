import csv, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"tools"))
from localization_common import controls, display_lines, immutable_tokens, visible_text
from validate_dialogues import validate, validate_translation_row
from validate_terminology import detect_canonical_terms_in_source, load_canonical, validate_assignments
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
            _,_,issues=validate(path,ROOT)
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

    def dialogue_issues(self,source,target,annotation=""):
        src={"source":source}; row={"id":"test","fr":target,"canonical_ids":annotation}
        return validate_translation_row(src,row,self.data)

    def assert_dialogue_ok(self,source,target,annotation=""):
        self.assertFalse(self.dialogue_issues(source,target,annotation))

    def assert_dialogue_error(self,source,target,annotation=""):
        self.assertTrue(any(level=="ERREUR" for level,_,_ in self.dialogue_issues(source,target,annotation)))

    def test_dialogue_charizard_canonical(self):
        self.assert_dialogue_ok("Charizard","Dracaufeu")

    def test_dialogue_charizard_invented_rejected(self):
        self.assert_dialogue_error("Charizard","Draconfeu")

    def test_dialogue_thunder_wave_canonical_longest_match(self):
        found=detect_canonical_terms_in_source("Thunder Wave",self.data)
        self.assertEqual([term["internal_id"] for term,_ in found],["MOVE_THUNDER_WAVE"])
        self.assert_dialogue_ok("Thunder Wave","Cage-Éclair")

    def test_dialogue_thunder_wave_invented_rejected(self):
        self.assert_dialogue_error("Thunder Wave","Vague de Tonnerre")

    def test_dialogue_annotated_thunder_invented_rejected(self):
        self.assert_dialogue_error("Thunder","Éclair Assassin","MOVE_THUNDER")

    def test_dialogue_annotated_thunder_canonical(self):
        self.assert_dialogue_ok("Thunder","Fatal-Foudre","MOVE_THUNDER")

    def test_dialogue_unannotated_thunder_requires_review(self):
        issues=self.dialogue_issues("Thunder","Fatal-Foudre")
        self.assertTrue(any(level=="REVIEW_REQUIRED" for level,_,_ in issues))

class PatchTest(unittest.TestCase):
    def test_bps_variable_length_integer_has_final_bit(self):
        self.assertEqual(number(0),b"\x80")
        self.assertEqual(number(127),b"\xff")
        self.assertEqual(number(128),b"\x00\x80")

if __name__=="__main__": unittest.main()
