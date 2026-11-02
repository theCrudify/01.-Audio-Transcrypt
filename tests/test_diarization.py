import unittest

from app.diarization import parse_vad_map, segment_words, speaker_for_segment, split_by_speaker, to_original_time


class SpeakerForSegmentTest(unittest.TestCase):
    TURNS = [(0.0, 5.0, 7), (5.0, 9.0, 3), (9.0, 12.0, 7)]

    def test_numbered_by_first_appearance(self):
        labels = {}
        self.assertEqual(speaker_for_segment(self.TURNS, 0.5, 4.0, labels), "Pembicara 1")  # raw speaker 7
        self.assertEqual(speaker_for_segment(self.TURNS, 6.0, 8.0, labels), "Pembicara 2")  # raw speaker 3
        self.assertEqual(speaker_for_segment(self.TURNS, 9.5, 11.0, labels), "Pembicara 1")

    def test_largest_overlap_wins(self):
        self.assertEqual(speaker_for_segment(self.TURNS, 4.5, 8.5, {}), "Pembicara 1")  # 0.5 s of 7 vs 3.5 s of 3 -> 3 first seen
        labels = {}
        speaker_for_segment(self.TURNS, 0.0, 1.0, labels)
        self.assertEqual(speaker_for_segment(self.TURNS, 4.5, 8.5, labels), "Pembicara 2")

    def test_no_overlap_is_unknown(self):
        self.assertEqual(speaker_for_segment(self.TURNS, 20.0, 21.0, {}), "Unknown")



def tok(text, start_ms, end_ms):
    return {"text": text, "offsets": {"from": start_ms, "to": end_ms}}


class VadMapTest(unittest.TestCase):
    LOG = (
        "whisper_vad: vad_segment_info: orig_start: 5.00, orig_end: 15.00, vad_start: 0.00, vad_end: 10.00\n"
        "whisper_vad: vad_segment_info: orig_start: 19.00, orig_end: 30.00, vad_start: 10.20, vad_end: 21.20\n"
    )

    def test_parse(self):
        self.assertEqual(parse_vad_map(self.LOG), [(5.0, 15.0, 0.0, 10.0), (19.0, 30.0, 10.2, 21.2)])

    def test_maps_compressed_time_back_to_original(self):
        vad_map = parse_vad_map(self.LOG)
        self.assertAlmostEqual(to_original_time(0.02, vad_map), 5.02)
        self.assertAlmostEqual(to_original_time(12.2, vad_map), 21.0)
        self.assertAlmostEqual(to_original_time(10.1, vad_map), 19.0)  # padding between chunks -> next chunk start

    def test_without_vad_time_is_unchanged(self):
        self.assertEqual(to_original_time(7.5, []), 7.5)


class SplitBySpeakerTest(unittest.TestCase):
    TURNS = [(0.0, 3.0, 4), (3.2, 4.5, 9), (4.6, 8.0, 4)]

    def test_subword_tokens_join_and_specials_are_skipped(self):
        segment = {"tokens": [tok("[_BEG_]", 0, 0), tok(" Ameri", 0, 300), tok("cans", 300, 600), tok(",", 600, 650)]}
        self.assertEqual(segment_words(segment, []), [(0.0, 0.65, " Americans,")])

    def test_short_reply_inside_one_whisper_line_gets_its_own_speaker(self):
        words = [(0.2, 1.0, " Jadi"), (1.0, 2.5, " begitu ya?"), (3.3, 3.8, " Iya"), (3.8, 4.4, " betul."), (4.7, 6.0, " Oke lanjut")]
        self.assertEqual(split_by_speaker(words, self.TURNS), [
            (0.2, 2.5, "Jadi begitu ya?", 4),
            (3.3, 4.4, "Iya betul.", 9),
            (4.7, 6.0, "Oke lanjut", 4),
        ])

    def test_tiny_blip_is_merged_back(self):
        turns = [(0.0, 2.0, 1), (2.0, 2.1, 2), (2.1, 5.0, 1)]
        words = [(0.0, 1.9, " satu dua"), (2.0, 2.1, " tiga"), (2.1, 4.0, " empat")]
        self.assertEqual(split_by_speaker(words, turns), [(0.0, 4.0, "satu dua tiga empat", 1)])


if __name__ == "__main__":
    unittest.main()
