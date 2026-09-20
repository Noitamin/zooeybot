"""Compatibility checks for image and voice dependency upgrades."""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from apng import APNG
from discord import VoiceClient
from nacl.secret import Aead
from PIL import Image

from utils.helpers import APNGtoGIF


class RuntimeDependencyTests(unittest.TestCase):
    def test_animated_sticker_conversion(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            frames = []
            for index, color in enumerate(('red', 'blue')):
                path = root / f'{index}.png'
                Image.new('RGBA', (16, 16), color).save(path)
                frames.append(str(path))
            APNG.from_files(frames, delay=100).save(str(root / 'animated.png'))
            APNGtoGIF(str(root / 'animated.png'))
            with Image.open(root / 'animated.gif') as result:
                self.assertEqual(result.n_frames, 2)
                self.assertEqual(result.size, (16, 16))
                result.seek(0)
                self.assertEqual(result.convert('RGB').getpixel((0, 0)), (255, 0, 0))
                result.seek(1)
                self.assertEqual(result.convert('RGB').getpixel((0, 0)), (0, 0, 255))

    def test_discord_voice_encryption_with_patched_pynacl(self):
        # Exercise Discord's packet encryption without opening a voice connection.
        client = object.__new__(VoiceClient)
        client._connection = SimpleNamespace(secret_key=bytes(range(Aead.KEY_SIZE)))
        client._incr_nonce = 0
        header = bytes(range(12))
        audio = b'test voice packet'
        packets = [client._encrypt_aead_xchacha20_poly1305_rtpsize(header, audio) for _ in range(2)]
        self.assertNotEqual(packets[0], packets[1])
        for packet in packets:
            nonce = packet[-4:] + bytes(20)
            self.assertEqual(packet[:12], header)
            self.assertEqual(Aead(client.secret_key).decrypt(packet[12:-4], header, nonce), audio)


if __name__ == '__main__':
    unittest.main()
