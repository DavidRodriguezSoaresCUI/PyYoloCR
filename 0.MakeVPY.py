

if __name__=='__main__':

    # Get video file
    from pathlib import Path
    while True:
        video_f = Path(input("Video file : "))
        if video_f.is_file():
            break
        print(f"Could not find '{video_f}' !")

    # Get VPY files
    VPYs = [
        Path(vpy)
        for vpy in ['./VPY/YoloResize.vpy', './VPY/YoloSeuil.vpy', './VPY/YoloCR.vpy']
    ]
    assert all([vpy.is_file() for vpy in VPYs]), f"ERROR: Could not find all VPY files : {VPYs}"

    # Output custom VPYs
    for vpy in VPYs:
        dest = Path(vpy.name)
        if dest.is_file():
            assert not dest.samefile(vpy)
        dest.write_text(
            vpy.read_text().replace('!!!VIDEOFILE!!!',str(video_f))
        )

