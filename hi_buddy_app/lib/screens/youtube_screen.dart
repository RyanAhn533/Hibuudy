import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';

/// 유튜브 인앱 재생 화면
/// videoId가 있으면 인앱 재생, searchQuery만 있으면 유튜브 앱/브라우저로 이동
class YouTubeScreen extends StatefulWidget {
  final String? videoId;
  final String? searchQuery;
  final String title;

  const YouTubeScreen({
    super.key,
    this.videoId,
    this.searchQuery,
    this.title = '영상 보기',
  });

  @override
  State<YouTubeScreen> createState() => _YouTubeScreenState();
}

class _YouTubeScreenState extends State<YouTubeScreen> {
  YoutubePlayerController? _controller;
  bool _isFullScreen = false;

  @override
  void initState() {
    super.initState();

    if (widget.videoId != null && widget.videoId!.isNotEmpty) {
      _controller = YoutubePlayerController(
        initialVideoId: widget.videoId!,
        flags: const YoutubePlayerFlags(
          autoPlay: true,
          mute: false,
          enableCaption: true,
          forceHD: false,
        ),
      );
    } else if (widget.searchQuery != null && widget.searchQuery!.isNotEmpty) {
      // videoId 없으면 유튜브 검색으로 이동
      _openYouTubeSearch();
    }
  }

  Future<void> _openYouTubeSearch() async {
    final query = Uri.encodeComponent(widget.searchQuery!);
    final url = Uri.parse('https://www.youtube.com/results?search_query=$query');
    try {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (_) {
      // 실패 시 무시
    }
    // 검색으로 이동한 경우 화면을 닫음
    if (mounted) {
      Navigator.of(context).pop();
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    // 전체화면에서 돌아올 때 세로 고정 해제
    SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // searchQuery만 있는 경우 로딩 표시 후 브라우저로 이동
    if (_controller == null) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.title)),
        body: const Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 20),
              Text(
                '유튜브로 이동 중이에요...',
                style: TextStyle(fontSize: 20),
              ),
            ],
          ),
        ),
      );
    }

    return YoutubePlayerBuilder(
      onExitFullScreen: () {
        setState(() => _isFullScreen = false);
        SystemChrome.setPreferredOrientations([
          DeviceOrientation.portraitUp,
        ]);
      },
      onEnterFullScreen: () {
        setState(() => _isFullScreen = true);
      },
      player: YoutubePlayer(
        controller: _controller!,
        showVideoProgressIndicator: true,
        progressIndicatorColor: HiBuddyColors.primary,
        progressColors: const ProgressBarColors(
          playedColor: HiBuddyColors.primary,
          handleColor: HiBuddyColors.primaryLight,
        ),
      ),
      builder: (context, player) {
        return Scaffold(
          appBar: _isFullScreen
              ? null
              : AppBar(
                  title: Text(
                    widget.title,
                    style: const TextStyle(fontSize: 20),
                  ),
                  leading: IconButton(
                    icon: const Icon(Icons.arrow_back, size: 28),
                    onPressed: () => Navigator.of(context).pop(),
                    tooltip: '뒤로 가기',
                  ),
                ),
          body: Column(
            children: [
              // 유튜브 플레이어
              player,

              // 컨트롤 영역
              if (!_isFullScreen) ...[
                const SizedBox(height: 24),

                // 제목 표시
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Text(
                    widget.title,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: HiBuddyColors.text,
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),

                const SizedBox(height: 32),

                // 큰 버튼들
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      // 재생/일시정지
                      _buildControlButton(
                        icon: Icons.play_arrow,
                        label: '재생',
                        onTap: () {
                          _controller!.play();
                        },
                      ),
                      _buildControlButton(
                        icon: Icons.pause,
                        label: '일시정지',
                        onTap: () {
                          _controller!.pause();
                        },
                      ),
                      // 전체화면
                      _buildControlButton(
                        icon: Icons.fullscreen,
                        label: '크게 보기',
                        onTap: () {
                          _controller!.toggleFullScreenMode();
                        },
                      ),
                    ],
                  ),
                ),

                const Spacer(),

                // 닫기 버튼
                Padding(
                  padding: const EdgeInsets.all(20),
                  child: SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton.icon(
                      onPressed: () => Navigator.of(context).pop(),
                      icon: const Icon(Icons.close, size: 28),
                      label: const Text(
                        '영상 닫기',
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: HiBuddyColors.danger,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildControlButton({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return Column(
      children: [
        SizedBox(
          width: 72,
          height: 72,
          child: ElevatedButton(
            onPressed: onTap,
            style: ElevatedButton.styleFrom(
              backgroundColor: HiBuddyColors.primaryBg,
              foregroundColor: HiBuddyColors.primary,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
                side: const BorderSide(color: HiBuddyColors.primaryLight),
              ),
              padding: EdgeInsets.zero,
            ),
            child: Icon(icon, size: 36),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: HiBuddyColors.text,
          ),
        ),
      ],
    );
  }
}
