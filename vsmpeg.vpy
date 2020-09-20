# vapoursynth
from vapoursynth import core
# std
import os
import math
import functools
import binascii
import subprocess
# pip packages
from pvsfunc.psourcer import PSourcer
from pvsfunc.pdeinterlacer import PDeinterlacer
from pvsfunc.helpers import anti_file_prefix
from pvsfunc import decimate, debox
from pyd2v import D2V
from pymediainfo import MediaInfo

# ============ #
# Installation #
# 1.  Run `pip install pvsfunc pyd2v`
# 2a. Windows: `where vsrepo.py`, copy the full path to vsrepo.py `python <path/to/vsrepo.py> install havsfunc mvsfunc d2v ffms2`.
# 2b. Linux: Install havsfunc, mvsfunc, d2v_source and ffms2, all are available on github and some distro user repos just search up.
# 3.  Download DGIndex v1.5.8 from http://rationalqm.us/dgmpgdec/dgmpgdec.html (its in dgmpgdec158.zip)
# 4a. Windows: Place DGIndex in C:/Program Files (x86)/DGIndex and then add that path to "PATH" with "Environment Variables" (start menu)
# 4b. Linux: Add it to system-wide path, wine will work don't worry, `sudo nano /etc/profile.d/env.sh` and just pop it into export $PATH
# 5.  Install MKVToolNix and make sure mkvmerge and mkvextract is available in PATH
# ============ #
# Usage #
# It's super simple, configure CFG and read what each option does.
# ===== #

CFG = {
	# print debugging information
	"debug": False,
	# choose file to import and use
	"file_path": r"file:///mnt/emby-1/tv/Family Guy/Family.Guy.S01.480p.DVD.REMUX.DD2.0.MPEG-PHOENiX/Family.Guy.S01E01.Death.Has.a.Shadow.480p.DVD.REMUX.DD2.0.MPEG-PHOENiX.mkv",
	"deinterlace": {
		# deinterlacer function to use, e.g. `"kernel": havsfunc.QTGMC`. `None` defaults to QTGMC
		"kernel": None,
		# arguments to pass to the kernel function
		"kernel_args": {
			# this is kernel arguments for QTGMC since it defaults to QTGMC
			# FPSDivisor: Some interlaced content can be Double-rate FPS, for example `The IT Crowd UK PAL DVD S01E03` is Double-rate FPS (50.000; 50/1), use `1` for Double-rate output, and `2` otherwise. With this set to `1` if every 2nd frame is a duplicate (or slightly different changes due to QTGMC interpretation) then it is NOT double-rate FPS and `2` should be used.
			"FPSDivisor": 2
			# ... add arguments based on qtgmc's documentation here if wanted: http://avisynth.nl/index.php/QTGMC
		}
	},
	"decimate": {
		# IVTC (Inverse-Telecine) a video by deleting frames with a pattern (mode=0) or by duplicate detection (mode=1)
		"enabled": False,
		"per_vob_id": True,
		#"mode": 0,  # mode 0 is recommended
		"cycle": [
			# cycles can be a list of integers, where each cycle corresponds to each vob id.
			# 5 is most common cycle for NTSC 3:2 pulldown, see if that one matches first
			5
		],
		"offsets": [
			# offsets can be a list of lists, where each offset corresponds to each vob id.
			# [0, 1, 3, 4] is most common offset, see if that one matches first
			[0, 2, 3, 4],
			#[0, 1, 3, 4]
		]
	},
	"chroma": {
		# Chroma Location allows you to change how it handles the Chroma Sub-sampling. You would typically use this if you notice
		# color bleeding, color bleeds outside where it's supposed to be, e.g. bleeding outside the edge of an object or outline.
		# See here: http://www.vapoursynth.com/doc/apireference.html#reserved-frame-properties
		# ! Important: Getting this value wrong can severely ruin the color quality. If unsure, put `None` !
		"location": None  # None==Default, options: 0..5, for MPEG-2, 0 (center-left) is "standard" but usually 2 (top-left) results in less chroma bleeding and may be more desirable.
	},
	"debox": {
		# Remove Pillarboxing or Letterboxing from the video by calculating a crop area based on aspect_ratio calculated against clip width and height.
		"enabled": False,
		#"aspect_ratio": "4:3",
		#"mode": 0,
		#"offset": 0
	},
	"vsgan": {
		# Super-resolution Generative Adversarial Network (port of ESRGAN). Allows you to use trained models on each frame of the video. VSGAN is applied after Deinterlacing, Decimation and Deboxing but before aspect_ratio fixer below.
		# https://github.com/rlaPHOENiX/VSGAN
		# if you dont care about this or have no clue how to use it just set enabled: false and move on lol
		"enabled": False,
		"compare": 1,  # Compare between input and output of VSGAN, 0=Off, 1==Interleave, 2==StackHorizontal, 3==mvsfunc.Preview
		"output_yuv": False,  # Convert Result frame to YUV, recommended if encoding to video with FFMPEG, otherwise disable
		"executions": [{
			"enabled": False,
			"model": r"/home/phoenix/github/BasicSR/experiments/sollevante/models/300000_G.pth",
			"scale": 4,
			"device": 1,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": False,
			"model": r"/home/phoenix/github/BasicSR/experiments/american-dad-s07e01/models/75000_G.pth",
			"scale": 4,
			"device": 0,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": False,
			"model": r"/home/phoenix/github/BasicSR/experiments/family-guy-its-a-trap/models/100000_G.pth",
			"scale": 4,
			"device": 0,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": True,
			"model": r"/home/phoenix/BasicSR-Xin/experiments/pokemon_br2remaster/models/200000_G.pth",
			"scale": 1,
			"device": 1,
			"chunk": False,
			"resample": 1080
		}]
	},
	"aspect_ratio": {
		# Resizes frame images to match the Aspect-Ratio provided by the Source Loader. However, this will round up the width value if it's not an int.
		# If possible, set Aspect-Ratio on the container rather than transcoding to that resolution, that way you have a bit more data on the width of the frames while still displaying at the wanted aspect-ratio on playback.
		"enabled": False,
		"kernel": core.resize.Spline64  # Good options are Spline64, Bicubic and Nearest-Neighbour/Point depending on what you need done.
	}
}

# = Main Code =
# Do not edit beyond here unless you know what your doing

# get file path from vspipe if passed
try:
	CFG["file_path"] = FILEPATH.decode("utf-8")
	CFG["debug"] = False
except NameError:
	pass

CFG["file_path"] = anti_file_prefix(CFG["file_path"])

mi = MediaInfo.parse(CFG["file_path"])
mi_video = [x for x in mi.tracks if x.track_type == "Video"]
if len(mi_video) > 0:
	mi_video = mi_video[0]
	if mi_video.original_frame_rate:
		# has a modified frame rate, lets restore back to original
		fps_fix_path = f"{CFG['file_path']}.fpsfix.mkv"
		original_fps = None
		if mi_video.framerate_original_num and mi_video.framerate_original_den:
			original_fps = f"{mi_video.framerate_original_num}/{mi_video.framerate_original_den}"
		else:
			original_fps = f"{mi_video.original_frame_rate}"
		if not os.path.exists(fps_fix_path):
			subprocess.check_output([
				"mkvmerge","--output", fps_fix_path,
				 "--default-duration", f"{mi_video.track_id-1}:{original_fps}fps",
				CFG["file_path"]
			], cwd=os.path.dirname(CFG["file_path"]))
		CFG["file_path"] = fps_fix_path

# Load file via pvsfunc.PSourcer
psourcer = PSourcer(CFG["file_path"], debug=CFG["debug"])
sourcer = psourcer.sourcer
clip = psourcer.clip

# Deinterlace via pvsfunc.PDeinterlacer
clip = PDeinterlacer(clip, **CFG["deinterlace"], debug=CFG["debug"]).clip

# Decimate
if CFG["decimate"]["enabled"]:
	clip = decimate(
		clip=clip,
		**{k: v for k,v in CFG["decimate"].items() if k not in ["enabled"]},
		debug=CFG["debug"]
	)

# Chroma
if type(CFG["chroma"]["location"]) is int:
	if CFG["chroma"]["location"] < 0 or CFG["chroma"]["location"] > 5:
		raise ValueError("CFG->chroma->location value is invalid. Must be an integer between 0..5")
	clip = core.resize.Point(clip, chromaloc=CFG["chroma"]["location"], chromaloc_in=clip.get_frame(0).props["_ChromaLocation"])

# Debox
if CFG["debox"]["enabled"]:
	clip = debox(
		clip,
		**{k: v for k,v in CFG["debox"].items() if k not in ["enabled"]}
	)

# VSGAN
if CFG["vsgan"]["enabled"]:
	import mvsfunc
	from vsgan import VSGAN
	if CFG["vsgan"]["compare"]:
		og = clip
	for execution in CFG["vsgan"]["executions"]:
		if not execution["enabled"]:
			continue
		vsgan_device = VSGAN(execution["device"])
		vsgan_device.load_model(
			model=execution["model"],
			scale=execution["scale"]
		)
		clip = vsgan_device.run(clip, chunk=execution["chunk"])
		if execution["resample"]:
			clip = core.resize.Spline36(
				clip,
				width=execution["resample"] * (clip.width / clip.height),
				height=execution["resample"]
			)
	if CFG["vsgan"]["output_yuv"]:
		clip = mvsfunc.ToYUV(clip, css="4:2:0", depth=8)
	if CFG["vsgan"]["compare"]:
		# match the res and format between the before clip and current clip
		if og.height != clip.height or og.width != clip.width:
			og = core.resize.Spline36(og, width=clip.width, height=clip.height)
		if og.format != clip.format:
			# assuming RGB24 as VSGAN returns an RGB24 clip, maybe check if RGB or YUV
			og = mvsfunc.ToRGB(og, depth=clip.format.bits_per_sample)
		clip = [
			core.text.Text(og, "Original"),
			core.text.Text(clip, "Result")
		]
		clip = core.std.Interleave(clip) if CFG["vsgan"]["compare"] == 1 else core.std.StackHorizontal(clip) if CFG["vsgan"]["compare"] == 2 else mvsfunc.Preview(clip)

# Aspect Ratio
if CFG["aspect_ratio"]["enabled"] and sourcer == "core.d2v.Source":
	d2v = D2V(clip.get_frame(0).props["PVSFilePath"])
	aspect_ratio = d2v.settings["Aspect_Ratio"]
	aspect_ratio_s = [int(x) for x in aspect_ratio.split(":")]
	calculated_width = clip.height * (aspect_ratio_s[0] / aspect_ratio_s[1])
	if CFG["vsgan"]["enabled"] and CFG["vsgan"]["compare"] == 2:
		# make the width double to accomodate vsgan compare mode 2 if used
		calculated_width = calculated_width * 2
	if calculated_width != math.ceil(calculated_width):
		aspect_ratio += f" [rounded]"
	clip = CFG["aspect_ratio"]["kernel"](clip=clip, width=math.ceil(calculated_width))

clip.set_output()
