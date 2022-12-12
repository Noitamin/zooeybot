import pip
import sys
# Automatically install dependencies when run

voice = input("Setup with voice (requires libffi) (y/n)? ")
if voice is "y" or voice is "Y":
    pip.main(["install", "discord.py[voice]"])
elif voice is "n" or voice is "N":
    pip.main(["install", "discord.py"])
else:
    print("Invalid option; aborting")
    sys.exit()

pip.main(["install", "requests"])
pip.main(["install", "pillow==5.0"])
pip.main(["install", "imageio"])
pip.main(["install", "apng"])
pip.main(["install", "tweepy"])
