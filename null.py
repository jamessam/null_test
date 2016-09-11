# !/usr/bin/env python
#
# Script: null.py
# Author: Jim Sam
#
# This Python 3.4 script performs a null test between similarly named WAV files
# in different directories. Following, it produces a report if the two files
# null, that is, if they're the same audio.
#

import datetime
import linecache
import platform
import re
import os
import subprocess

class AFile:
    def open_file(self, f):
        self.open_file = open(f, 'a', encoding='utf-8')
    def write_to_file(self, term):
        self.open_file.write(term)
    def close_file(self):
        self.open_file.close()
    count = 0


def run_command(command, terminal):
    output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    message = output.stdout.read()
    terminal.write_to_file("\r\nCommand " + str(command) + "\r\n")
    if len(message) > 1:
        terminal.write_to_file(message+"\r\n")
    return message

def getLoud(file, path):
    command = ['ffmpeg','-i', path+file, '-af', 'volumedetect', '-f', 'null', 'NUL']
    yo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in yo.stdout:
        if 'max_volume' in line:
            line = line.rstrip()
            volume = line[line.find(':')+2:]

    volume = volume.rstrip()
    return volume

def check_channels(file, path):
    command = ['ffmpeg','-i', path+file, '-af', 'volumedetect', '-f', 'null', 'NUL']
    yo = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

    for line in yo.stdout:
        if 'mono' in line:
            channels = 1

        if 'stereo' in line:
            channels = 2

    return channels

def sixteen_bit(path, f, terminal):
    sixteen = f.split('.')[0]+"_16bit.wav"
    command = ['ffmpeg','-i',path+f, '-dither_method','modified_e_weighted', path+sixteen]
    output = run_command(command, terminal)
    return sixteen

def null_test(path1, path2, f, terminal):
    does_null = False
    channels = check_channels(f, path1)
    print("Working on %s now." % f)

    # Create 16-bit files
    sixteen_a = sixteen_bit(path1, f, terminal)
    sixteen_b = sixteen_bit(path2, f, terminal)

    # Invert file in path2
    inverted = sixteen_b.split('.')[0]+"_i.wav"
    if channels == 1:
        inv_command = ['ffmpeg','-i', path2+sixteen_b, '-af', 'aeval=-val(0)', path2+inverted]
    else:
        inv_command = ['ffmpeg','-i', path2+sixteen_b, '-af', 'aeval=-val(0)|-val(1)', path2+inverted]
    output = run_command(inv_command, terminal)

    # Mix files together
    mixed = f.split('.')[0]+"-mix.wav"
    mix_command = ['ffmpeg','-i',path1+sixteen_a,'-i',path2+inverted,'-filter_complex','amix',path2+mixed]

    output = run_command(mix_command, terminal)

    # toggle does_null based on volume of mixed file.
    peak = getLoud(mixed, path2)
    if peak == '-91.0 dB' or peak == '.0 dB':
        does_null = True

    # Remove the inverted and mixed files
    os.remove(path1+sixteen_a)
    os.remove(path2+sixteen_b)
    os.remove(path2+inverted)
    os.remove(path2+mixed)

    return does_null

def make_file_list(path1, path2):
    d1 = os.listdir(path1)
    file_list = []
    not_in_both = []

    audio_extentions = ['wav', 'flac', 'mp3']

    for f in d1:
        file_name=f.split('.')
        if file_name[1] not in audio_extentions:
            continue

        f2 = os.path.join(path2, f)
        if os.path.exists(f2):
            file_list.append(f)
        else:
            not_in_both.append(f)

    return file_list, not_in_both

def validate_path(path):
    re_result = re.match(r'^(\w:\\$)|(\w:\\).*\\$|^(/.*/)$', path)
    os_result = os.path.exists(path)
    if re_result and os_result:
        result = True
    else:
        result = False

    return result

def get_paths():
    toggle = False
    while toggle==False:
        path1 = input("Where is the master directory? ")
        path2 = input("Where is the second directory? ")
        a = validate_path(path1)
        b = validate_path(path2)
        if a and b:
            toggle=True
            print()
        else:
            print('\nAt least one of those paths was invalid. Please try again.\n')

    return path1, path2

def main():
    path1, path2 = get_paths()
    file_list, not_in_both = make_file_list(path1, path2)

    terminal = AFile()
    terminal.open_file(path1+str(datetime.date.today())+'_terminal_output.txt')

    same = []
    different = []

    for f in file_list:
        does_null = null_test(path1, path2, f, terminal)
        if does_null:
            same = same + [f]
        else:
            different = different + [f]

    with open(path1+'results.txt', 'w') as results:
        # Write what did null
        results.write("These files are the same:\r\n")
        for f in same:
            results.write(f+"\r\n")

        # Write what did not null
        results.write("\r\nThese files are different:\r\n")
        for f in different:
            results.write(f+"\r\n")

        # Write into results what files were ignored
        results.write("\r\nThe following files were ignored because they were not in the second directory.\r\n")
        for f in not_in_both:
            results.write(f+"\r\n")

    terminal.close_file()

    # Assistance with the following six lines of code was from StackOverlow
    # user Cas - http://stackoverflow.com/users/175584/cas
    # http://stackoverflow.com/questions/6631299/python-opening-a-folder-in-explorer-nautilus-mac-thingie
    # Creative Commons license outlined at http://blog.stackoverflow.com/2009/06/attribution-required/
    if platform.system() == "Windows":
        os.startfile(path1+'results.txt')
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", path1+'results.txt'])
    else:
        subprocess.Popen(["xdg-open", path1+'results.txt'])


if __name__ == '__main__':
    main()