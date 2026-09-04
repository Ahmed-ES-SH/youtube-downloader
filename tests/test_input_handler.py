from unittest.mock import MagicMock, patch

from components.input_handler import detect_url_type, is_valid_youtube_url


def test_valid_video_url():
    assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True


def test_valid_playlist_url():
    assert is_valid_youtube_url("https://www.youtube.com/playlist?list=PLxxx") is True


def test_valid_shorts_url():
    assert is_valid_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True


def test_valid_mobile_url():
    assert is_valid_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True


def test_valid_music_url():
    assert is_valid_youtube_url("https://music.youtube.com/watch?v=dQw4w9WgXcQ") is True


def test_valid_shortener_url():
    assert is_valid_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True


def test_invalid_url():
    assert is_valid_youtube_url("https://vimeo.com/123456") is False


def test_empty_url():
    assert is_valid_youtube_url("") is False


@patch("components.input_handler.yt_dlp.YoutubeDL")
def test_detect_playlist(mock_ydl):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        "_type": "playlist",
        "title": "Test Playlist",
        "entries": [{"title": "Vid 1", "url": "..."}, {"title": "Vid 2", "url": "..."}],
    }
    mock_ydl.return_value.__enter__.return_value = mock_instance

    result = detect_url_type("https://youtube.com/playlist?list=PLtest")
    assert result["type"] == "playlist"
    assert result["count"] == 2


@patch("components.input_handler.yt_dlp.YoutubeDL")
def test_detect_single_video(mock_ydl):
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {
        "_type": "video",
        "title": "Single Video",
        "webpage_url": "https://youtube.com/watch?v=abc",
    }
    mock_ydl.return_value.__enter__.return_value = mock_instance

    result = detect_url_type("https://youtube.com/watch?v=abc")
    assert result["type"] == "video"
    assert result["count"] == 1
