# VSMPEG

VapourSynth script to automatically handle fields of an MPEG video file to return a Progressive CFR video stream.

# What is VapourSynth and what is a VapourSynth Script (.vpy)

"A video processing framework with simplicity in mind"—[VapourSynth Project](https://github.com/vapoursynth/vapoursynth)

To add more to that, It's a Script-based NLE ([Non-linear editing system](https://wikipedia.org/wiki/Non-linear_editing_system)), meaning it isn't a GUI program, all changes you wish to make must be specifically programmed in [Python](https://wikipedia.org/wiki/Python_(programming_language)), hence the VapourSynth Script project extension, .vpy.

# No GUI?! That must be painful!

For your typical YouTube video it's unconventional yes, but that isn't the goal of a project like this. A Script-based NLE is to be scripted to do handle a specific use case, and be able to be utilised by other programs like GUI editors, video players, hardware players, and such.

This project (VSMPEG) is a great example of a use-case of VapourSynth as it deals with the shenanigans of MPEG video entirely automated (depending on the optional stuff you enable/want to do). This script isn't realtime right now, even on high-end hardware, however, if it becomes the case of the deinterlacing algorithms to shrink in processing time or hardware to improve, this script could be used in realtime as sort of an intermediate layer or plugin to automatically handle DVD playback automatically without any configuration by the user. That would be awesome.

# Installation

- I will presume you know what a terminal (or command prompt) is, and how to open one.
- When I state, "Run `...`" that indicates to run a command in a terminal.
- Run `python --version`, if that doesn't return v3.x.x, then `python` is a Python v2 (deprecated) binary. Run `python3` and if that works, then use that in-place of `python` in all following commands.

## Requirements

1. [VapourSynth](http://vapoursynth.com), seriously try and use the latest version for this one at all times.
1. [Python](https://python.org), it's needed for VapourSynth, read VapourSynth's installation guide for information on required versions.
2. [MKVToolNix](https://mkvtoolnix.download), ensure it's a recent version if not the latest.
3. [dgmpgdec158.zip](http://rationalqm.us/dgmpgdec/dgmpgdec.html) for DGIndex v1.5.8. Download and extract it to a folder named `dgmpgdec158`.
4. Linux ONLY: [wine](https://winehq.org) to be able to use DGIndex v1.5.8.

**Important**: Do not attempt to use an alternative MPEG indexer like D2VWitch or ffmpeg's indexer. They don't have nearly as much accuracy or efficiency as DGIndex as well as a few bugs I have noticed. DGIndex while old, is incredibly well made by Donald Graft and I want to thank him for his work on it.

## Dependencies

### Python

1. `python -m pip install --user pvsfunc pyd2v`

### VapourSynth

#### Windows:

1. Run `where vsrepo.py` and copy the full path it gives you.
2. `python <path/to/vsrepo.py> install havsfunc mvsfunc d2v ffms2`.

#### Linux:

1. It needs havsfunc, mvsfunc, d2v_source, and ffms2.
2. All are available on GitHub, you're on Linux you know the deal.
3. Go compile and install it, or use you're distro's AUR/User-Repository and hope it's on it.

### DGIndex

#### Windows:

1. Move the `dgmpgdec158` folder (which should contain `DGIndex.exe` to `C:/Program Files (x86)/dgmpgdec158` (or something similar, but I recommend in `C:/Program Files (x86)`.
2. Add that location to the `SYSTEM`'s `PATH` environment variable. ([how to add to path environment variable](https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/))
3. Close all terminal's you opened and open a new one before continuing to refresh the environment variable.

#### Linux:

1. Move the `dgmpgdec158` folder somewhere, it's linux, so it's up to you. I place all my portable Windows applications in `~/winbin`.
2. Add the location of `dgmpgdec158` to system-wide PATH environment variable, it MUST be REAL system-wide and not your shell's environment!  
`sudo nano /etc/profile.d/env.sh`, e.g.: `export PATH="$PATH:$HOME/winbin/dgmpgdec158"` where `~/winbin/dgmpgdec158` is where `DGIndex.exe` resides.
3. You might need to logout and log back in, or worst case scenario reboot. If you want to be safe, reboot now.
