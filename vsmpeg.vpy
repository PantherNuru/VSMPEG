#!/usr/bin/env python3

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
from pvsfunc.pdebox import PDebox
from pvsfunc.pdecimate import PDecimate
from pvsfunc.helpers import anti_file_prefix
from pyd2v import D2V
from pymediainfo import MediaInfo


"""
1. INSTALLATION

Follow instructions here: https://github.com/rlaPHOENiX/VSMPEG/blob/master/README.md

2. USAGE

It's super simple, configure the CFG variable found below.
"""


CFG = {
	# print useful information about the source video
	"debug": True,
	# choose video file to use, support's all kinds of formats and containers
	"file_path": r"file:///mnt/emby-red/tv/Family Guy/Family.Guy.S01.480p.DVD.REMUX.DD2.0.MPEG-PHOENiX/Family.Guy.S01E01.Death.Has.a.Shadow.480p.DVD.REMUX.DD2.0.MPEG-PHOENiX.mkv",
	# the deinterlacer options
	"deinterlace": {
		# deinterlacer function to use, e.g. `"kernel": havsfunc.QTGMC`. `None` defaults to Havsfunc's QTGMC
		"kernel": None,
		# arguments to pass to the kernel function
		"kernel_args": {
			# the following arguments are for havsfunc's QTGMC since kernel is set to `None`.
			# FPSDivisor: Some interlaced content can be Double-rate FPS, for example The IT Crowd's UK PAL DVD can be output as Double-rate FPS (50.000; 50/1) if you set to `1`. With it set to `1` and every 2nd frame is a duplicate (or slightly different changes due to QTGMC interpolation) then it is NOT double-rate FPS and `2` should be used.
			"FPSDivisor": 2
			# ... add more qtgmc arguments here if wanted: http://avisynth.nl/index.php/QTGMC
		}
	},
	"decimate": {
		# """
		# IVTC (Inverse-Telecine) a video by deleting frames in a pattern or by duplicate detection.
		#
		# Important: If you're IVTC'ing a DVD, you seriously have to provide this script a .vob file rather
		# than a .mp4/.mkv e.t.c. Do NOT use a REMUX or transcode of a DVD, you have to use the original .VOB.
		# This is because transcodes and remuxes don't retain vital VOB ID information crucial to ensuring
		# the decimation cycle stay's synced with the video.
		#
		# > You will need an understanding of Pulldown:
		#
		# https://gist.github.com/rlaPHOENiX/eaa987f7fd365fcd6803576746471b8d#6-pulldown
		#
		# > What is the Cycle?
		#
		# The cycle is the grouping/chunking of frames in which it will use the offsets information to decide
		# which frames of the cycle to keep or not. E.g. a cycle of `5` and an offset of `[0, 1, 2, 3]` will
		# remove every 5th frame.
		#
		# It's hard to explain how to retrieve what cycle value to use as it can literally be anything.
		# It all depends on how the video was encoded and prepared. I can give you an example however:
		#
		# Let's say you have FILM (24 fps) content and you want to play it on an NTSC CRT TV by broadcast or
		# DVD, then you would need to play it in 30000/1001 FPS (or 60000/1001 fields) no matter what.
		# How would you convert 24 fps to 30000/1001 (29.97~ FPS)? By pulldown. There's two ways, by telling
		# the player software or hardware to apply pulldown on playback, or by doing the pulldown right away
		# when encoding the video.
		#
		# For 24 FPS to 30000/1001 FPS you would delete 1 in every 1000 frames (or slow down the video by
		# 1.001 frame/s), and then apply Pulldown 2:3 meaning the first frame would be split into 2 fields
		# and the second frame would be split into 3 fields, repeating until all frames of the FILM video
		# is converted to just fields. What you end up with is 60000/1001 Field/s, or 30000/1001 Frame/s.
		# This means a cycle of 5 (Pulldown 2:3 == 2+3 == 5) would have been used here. After deinterlacing
		# the duplicate frame would be the 3rd frame every 5 frames would be a duplicate frame. For Pulldown 3:2
		# the duplicate frame would be the 2nd frame every 5 frames.
		#
		# > What is the Offset?
		#
		# Offset indicates which frames to keep, and which frames to delete in the cycle.
		#
		# The format of offsets are a list of integers in which each integer number represents each frame
		# in the cycle starting with 0. e.g. `3` would be the 4th frame in the cycle.
		# The maximum value of an integer in an offset would be the cycle number subtracted by 1, e.g. (5-1=4).
		# The maximum amount of integers in an offset would be the cycle number as it is.
		#
		# For an example, if our Cycle is 5, and we use the offsets: `[1, 3]`, that would delete the first
		# frame, the third frame, and the fifth frame, leaving only frame 2 and 4.
		#
		# > How do I IVTC?
		#
		# You need to find the correct values for Cycle and Offsets for your specific video.
		# You would only ever IVTC if you notice duplicate frames in a pattern so that you can delete unnecessary
		# frames and reduce file size and bitrate. So the first step really would be to try and notice a pattern
		# of duplicate frames.
		#
		# If you go frame by frame on a video (recommended doing so through this script, not in a video player)
		# and notice duplicate frames appearing in a pattern (e.g. every 5 frames, every 9 frames, e.t.c), then
		# you may need to IVTC.
		#
		# Make sure that scenes that would be typically done in post-production/editing like fade-in/outs, 
		# transitions, effects, credits, e.t.c are also having the same repeated pattern. If these shots don't
		# have duplicate frames then the video itself was edited in a higher frame rate than the actual video
		# contents. Meaning if you were to IVTC, you would make those edit's have less frames since they don't
		# have duplicates. For example on DVD's it's quite common for Intro's and Outro's to be 30000/1001 FPS
		# whereas the actual episode content is only 24000/1001 FPS but encoded with Pulldown 2:3 (or such) to
		# 30000/1001 FPS, resulting in a pattern of duplicate frames. In cases like this, it's up to you if you
		# want to IVTC or not, my point is just to make sure the entire video has the repeating pattern, and not
		# just one scene or just coincidence.
		#
		# Once you find a repeating duplicate pattern, go onto a frame that would be the duplicate (the 2nd frame
		# that's a copy), and enable "debug" and IVTC, go forward and count how many frames there are between each
		# duplicate (including the duplicate frame), and that's probably your Cycle, you would need to check this
		# multiple times throughout many scenes to confirm it.
		#
		# Now, fill up your offsets to keep every frame from the cycles, and test each frame removed on it's own
		# until the Debug display states "decimated_frame=True" only on the repeating duplicate frames.
		#
		# Verify "decimated_frame=True" is stated on all the pattern duplicate frames throughout the video and
		# only on the pattern duplicate frames.
		#
		# > Teacher's answer's sheet
		#
		# If you're video is 2:3 Pulldown (cycle of 5, duplicate every 5 frames) then the Offsets are most likely
		# going to be `[0, 1, 3, 4]` (delete cycle's third frame) or `[0, 2, 3, 4]` (delete cycle's second frame).
		# 
		# Anyway, never take any of these values as definites, just examples, always verify using "debug" if
		# "decimated_frame=True" on the right frames before finalising your values.
		#
		# Yes, IVTC is a pain in the ass, you gotta deal with it or just leave it as is, up to you.
		# Don't take shortcuts, measure twice and cut once. It's worse to use wrong values and encode it,
		# than leaving it as it is.
		#
		# """
		"enabled": False,
		# a dvd vob can contain more than one encoded video, this is indicated by vob id. decimation cycles should
		# always reset whenever it enters a new vob id (different video in same vob) or it will desync and delete
		# the wrong frames. it's safe to keep this enabled even on non dvd videos. this will only work if you provide
		# this script a dvd .vob file, not a remux of the dvd file, e.g. .mp4 or .mkv file.
		"per_vob_id": True,
		# decimation mode to use. mode 0 is default and recommended. mode 1 can be deadly: https://git.io/avoid-tdecimate
		"mode": 0,
		# decimation cycle, it's hard to explain this one, but think of it as grouping n frames and then
		# using the offsets information below to decide which of those frames to keep, then repeating for the next
		# group of those n frames.
		"cycle": [
			# cycles can be a list of integers, where each integer corresponds to each vob id.
			# if only one integer is specified, and there's more than one vob id, it will use that
			# integer for all vob id's.
			# for 3:2/2:3 pulldown, 5 is the most common cycle, see if that one matches first.
			5
		],
		"offsets": [
			# offsets must be a list of lists which has integers, where each integer corresponds to each vob id.
			# if only one list of integers is specified, and there's more than one vob id, it will use that
			# list of integers for all vob id's.
			# for 3:2/2:3 pulldown, [0, 1, 3, 4] is the most common offset, see if that one matches first.
			[0, 1, 3, 4],
			#[0, 2, 3, 4]
		]
	},
	"chroma": {
		# """
		# Chroma Location specifies the position of Chroma Sub-sampling.
		#
		# Generally speaking you would keep this set to `None` for it to automatically use what's recommended by
		# the codec's specifications sheet or what would of been the most common.
		#
		# However, if you notice color bleeding outside the edges of detail then the chroma location may be incorrect.
		# You can use this to change the location in the hopes that it will help. Do not get this mixed up with
		# color shifting, this isn't the same thing.
		#
		# At times though the encoding process can often take the original source videos they used to edit up
		# the video with using wrong chroma location values, and then encode the wrong location baking it into the video
		# and then also return the wrong chroma location on the new exported video. This happened on the first couple of
		# seasons of Family Guy NTSC USA DVD's, but didn't happen on the Family Guy PSP UMD-Video encodes thanks to the
		# AVC encoder they used for that, rather than the MPEG encoder they used for the DVD's.
		# If that happened, changing the Chroma Location will help, but wont fully shove the color back into place.
		#
		# Values:
		# `None` = Auto
		# 0 = Left (middle)
		# 1 = Center
		# 2 = Top-left
		# 3 = Top (middle)
		# 4 = Bottom-left
		# 5 = Bottom (middle)
		# ! Important: Getting this value wrong can severely ruin the color quality. If unsure, put `None` !
		# """
		"location": None
	},
	"debox": {
		# """
		# Remove Pillarboxing or Letterboxing by calculating a crop area based on aspect_ratio against clip width and height.
		# 
		# Mode:
		# 0 = Remove Pillarboxing
		# 1 = Remove Letterboxing
		#
		# Offset:
		# If there's slightly more boxing on one side than the other, you can use offset to re-center the cropping (- or + int).
		# """
		"enabled": False,
		"aspect_ratio": "4:3",
		#"mode": 0,
		#"offset": 0
	},
	"vsgan": {
		# """
		# Super-resolution Generative Adversarial Network (port of ESRGAN).
		# Allows you to use trained models on each frame of the video.
		# VSGAN is applied after Deinterlacing, Decimation and Deboxing but before aspect_ratio fixer below.
		
		# More info: 
		# https://github.com/rlaPHOENiX/VSGAN
		# """
		"enabled": False,
		"compare": 1,  # Compare between input and output of VSGAN, 0=Off, 1==Interleave, 2==StackHorizontal, 3==mvsfunc.Preview
		"output_yuv": False,  # Convert Result frame to YUV, recommended if encoding to video with FFMPEG, otherwise disable
		"executions": [{
			"enabled": True,
			"model": r"/home/phoenix/github/BasicSR-dev2/experiments/pkmnIntroLineClean/models/35000_G.pth",
			"device": 0,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": False,
			"model": r"/home/phoenix/Desktop/experiments/SpongeBob.CEL.2.HD.125ki.499e.16.208psnr-PHOENiX.pth",
			"device": 0,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": True,
			"model": r"/home/phoenix/github/BasicSR-dev2/experiments/pkmnbd2hd/models/80000_G.pth",
			"device": 0,
			"chunk": False,
			"resample": 1080
		}, {
			"enabled": False,
			"model": r"/home/phoenix/github/BasicSR/experiments/old_models/pokemon_br2remaster.pth",
			"device": 1,
			"chunk": False,
			"resample": 1080
		}]
	},
	"aspect_ratio": {
		# """
		# Convert the aspect ratio of the stored frames from rectangular PAR to square PAR.
		# Note: This will round up the width or height value if it's not an int.
		#
		# Mode 0 does less interpolation and fewer pixels, Mode 1 keeps all pixels and instead
		# of squashing it interpolates and stretches the height resulting in MORE pixels.
		#
		# Fewer pixels from mode 0 does not necessarily indicate a lower resolution or compressed
		# image.
		#
		# Just so you know, you can specify the Display aspect ratio on the encoded video on MP4 or MKV
		# within the container's metadata, using this option isn't directly needed.
		# """
		"enabled": False,
		"mode": 0,  # 0 == squash width, 1 == stretch height
		#"forced_ar": [16, 9],
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
	clip = PDecimate(
		clip=clip,
		**{k: v for k,v in CFG["decimate"].items() if k not in ["enabled"]},
		debug=CFG["debug"]
	).clip

# Chroma
if type(CFG["chroma"]["location"]) is int:
	if CFG["chroma"]["location"] < 0 or CFG["chroma"]["location"] > 5:
		raise ValueError("CFG->chroma->location value is invalid. Must be an integer between 0..5")
	clip = core.resize.Point(clip, chromaloc=CFG["chroma"]["location"], chromaloc_in=clip.get_frame(0).props["_ChromaLocation"])

# Debox
if CFG["debox"]["enabled"]:
	clip = PDebox(
		clip,
		**{k: v for k,v in CFG["debox"].items() if k not in ["enabled"]}
	).clip

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
		vsgan_device.load_model(anti_file_prefix(execution["model"]))
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
	aspect_ratio_s = CFG["aspect_ratio"]["forced_ar"] if "forced_ar" in CFG["aspect_ratio"] else [int(x) for x in aspect_ratio.split(":")]
	calculated_width = clip.height * (aspect_ratio_s[0] / aspect_ratio_s[1])
	calculated_height = clip.width / (aspect_ratio_s[0] / aspect_ratio_s[1])
	if CFG["vsgan"]["enabled"] and CFG["vsgan"]["compare"] == 2:
		# make the width double to accomodate vsgan compare mode 2 if used
		calculated_width = calculated_width * 2
	if calculated_width != math.ceil(calculated_width):
		aspect_ratio += f" [rounded]"
	# Convert from rectangular PAR to square PAR by:
	if CFG["aspect_ratio"]["mode"] == 0:
		# squashing width
		clip = CFG["aspect_ratio"]["kernel"](clip=clip, width=math.ceil(calculated_width))
	elif CFG["aspect_ratio"]["mode"] == 1:
		# stretching height
		clip = CFG["aspect_ratio"]["kernel"](clip=clip, height=math.ceil(calculated_height))

clip.set_output()
