import sys

import click

from components.input_handler import detect_url_type, is_valid_youtube_url
from components.prompt_handler import (
    get_download_options,
    ask_skip_or_abort,
    ask_trim_settings,
    confirm_download,
    select_playlist_items,
    select_playlist_range,
    select_playlist_range_bounds,
    validate_time,
    time_to_seconds,
)
from components.queue_manager import QueueManager, ItemStatus
from components.downloader import Downloader, DownloadError
from components.config_handler import load_config, save_config, AppConfig
from utils.logger import (
    print_banner,
    print_detection,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_summary,
)


@click.command()
@click.option("--url", "-u", default=None, help="YouTube video or playlist URL to download")
@click.option("--use-defaults", is_flag=True, help="Skip all interactive prompts, use saved config values instead")
@click.option("--trim-start", "-ts", default=None, help="Trim start time in MM:SS or HH:MM:SS format (requires --trim-end)")
@click.option("--trim-end", "-te", default=None, help="Trim end time in MM:SS or HH:MM:SS format (requires --trim-start)")
def main(url: str | None, use_defaults: bool, trim_start: str | None, trim_end: str | None):
    config = load_config()

    print_banner()

    if not url:
        from InquirerPy import inquirer
        url = inquirer.text(message="Enter YouTube URL:").execute()

    if not is_valid_youtube_url(url):
        print_error("Invalid YouTube URL. Please try again.")
        sys.exit(1)

    try:
        info = detect_url_type(url)
    except Exception as e:
        print_error(f"Failed to fetch URL info: {e}")
        sys.exit(1)

    if info["type"] == "playlist":
        print_detection(f'Playlist \u2014 "{info["title"]}" ({info["count"]} videos)')
    else:
        print_detection(f'Video \u2014 "{info["title"]}"')

    if info["count"] == 0:
        print_warning("No videos found.")
        sys.exit(0)

    if trim_start and not trim_end:
        print_error("--trim-start requires --trim-end")
        sys.exit(1)
    if trim_end and not trim_start:
        print_error("--trim-end requires --trim-start")
        sys.exit(1)

    options = get_download_options(config, use_defaults)

    if trim_start and trim_end:
        for t in (trim_start, trim_end):
            result = validate_time(t)
            if result is not True:
                print_error(f"Invalid trim time '{t}': {result}")
                sys.exit(1)
        if time_to_seconds(trim_start) >= time_to_seconds(trim_end):
            print_error("Trim start time must be before end time.")
            sys.exit(1)
        options["trim"] = {"start_time": trim_start, "end_time": trim_end}
    elif not use_defaults:
        trim = ask_trim_settings()
        if trim:
            options["trim"] = trim

    entries = info["entries"]
    if info["type"] == "playlist":
        if use_defaults:
            options["playlist_items"] = "1-999999"
            entries = [{"url": url, "title": f"Full playlist: {info['title']}"}]
            options["playlist_range"] = {"start": 1, "end": info["count"], "total": info["count"]}
        else:
            from InquirerPy.base.control import Choice
            from InquirerPy import inquirer as inq
            mode = inq.select(
                message=f"Playlist has {info['count']} videos. Select by:",
                choices=[
                    Choice("range", "Range (start to end)"),
                    Choice("individual", "Individual (checkbox)"),
                ],
            ).execute()
            if mode == "range":
                start, end = select_playlist_range_bounds(info["count"])
                options["playlist_items"] = f"{start}-{end}"
                options["playlist_range"] = {"start": start, "end": end, "total": info["count"]}
                entries = [{"url": url, "title": f"Playlist items {start}-{end}"}]
            else:
                selected = select_playlist_items(entries)
                if selected:
                    entries = selected

    if not confirm_download(len(entries), options["output"], options):
        print_info("Download cancelled.")
        sys.exit(0)

    queue = QueueManager(entries)
    downloader = Downloader()

    for item in queue.pending():
        label = item.title
        print_info(f'Downloading [{item.index}/{len(queue.items)}] \u2014 "{label}"')
        try:
            downloader.download(item, options)
            queue.mark_done(item)
            print_success(f"[{item.index}/{len(queue.items)}] Done")
        except DownloadError as e:
            queue.mark_failed(item, str(e))
            print_error(f"[{item.index}/{len(queue.items)}] Failed \u2014 {e}")
            if not ask_skip_or_abort():
                break
        except KeyboardInterrupt:
            print_warning("\nInterrupted by user.")
            break

    summary = queue.summary()
    print_summary(summary["done"], summary["failed"], summary["total"])

    if config.remember_last:
        config.default_format = options["format"]
        config.default_quality = options["quality"]
        if options.get("audio_bitrate"):
            config.default_audio_bitrate = options["audio_bitrate"]
        config.default_output_path = options["output"]
        save_config(config)


if __name__ == "__main__":
    main()
