import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/haru_agent.dart';
import '../services/tts_service.dart';
import 'youtube_screen.dart';
import 'timer_screen.dart';

/// 채팅 메시지 모델
class _ChatMessage {
  final String text;
  final bool isUser;
  final List<AgentAction> actions;
  final String? youtubeQuery;

  const _ChatMessage({
    required this.text,
    required this.isUser,
    this.actions = const [],
    this.youtubeQuery,
  });
}

class AgentScreen extends StatefulWidget {
  const AgentScreen({super.key});

  @override
  State<AgentScreen> createState() => _AgentScreenState();
}

class _AgentScreenState extends State<AgentScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();
  final _focusNode = FocusNode();
  bool _isLoading = false;

  final List<_ChatMessage> _messages = [
    _ChatMessage(
      text: '안녕하세요! 뭐든 물어보세요.',
      isUser: false,
      actions: [
        AgentAction(label: '오늘 일정 보기', actionType: 'navigate', data: {'screen': 'today'}),
        AgentAction(label: '운동하기', actionType: 'navigate', data: {'screen': 'exercise'}),
        AgentAction(label: '요리 도움', actionType: 'navigate', data: {'screen': 'recipes'}),
      ],
    ),
  ];

  @override
  void initState() {
    super.initState();
    TtsService.speak('안녕하세요! 뭐든 물어보세요.');
  }

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    TtsService.stop();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading) return;

    _textController.clear();

    setState(() {
      _messages.add(_ChatMessage(text: trimmed, isUser: true));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await HaruAgent.handle(trimmed);

      if (!mounted) return;
      setState(() {
        _messages.add(_ChatMessage(
          text: response.text,
          isUser: false,
          actions: response.actions,
          youtubeQuery: response.youtubeQuery,
        ));
        _isLoading = false;
      });
      _scrollToBottom();

      // TTS로 응답 읽어주기
      TtsService.speak(response.text);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _messages.add(const _ChatMessage(
          text: '죄송해요, 문제가 생겼어요. 다시 시도해 주세요.',
          isUser: false,
        ));
        _isLoading = false;
      });
      _scrollToBottom();
    }
  }

  void _handleAction(AgentAction action) {
    // 액션 타입에 따라 처리
    switch (action.actionType) {
      case 'youtube':
        final videoId = action.data['videoId'] as String?;
        final query = action.data['query'] as String? ?? '';
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => YouTubeScreen(
              videoId: videoId,
              searchQuery: query.isNotEmpty ? query : null,
              title: action.label,
            ),
          ),
        );
        break;
      case 'timer':
        final minutes = (action.data['minutes'] as num?)?.toInt() ?? 1;
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => TimerScreen(
              minutes: minutes,
              label: action.label,
            ),
          ),
        );
        break;
      case 'call':
        final name = action.data['name'] as String? ?? '';
        _sendMessage('$name 전화');
        break;
      default:
        // navigate, recipe 등은 라벨 텍스트를 다시 보내기
        _sendMessage(action.label);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('도우미'),
      ),
      body: Column(
        children: [
          // ── 채팅 메시지 리스트 ──
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: _messages.length + (_isLoading ? 1 : 0),
              itemBuilder: (context, index) {
                if (index == _messages.length && _isLoading) {
                  return _buildLoadingBubble();
                }
                return _buildMessageBubble(_messages[index]);
              },
            ),
          ),

          // ── 하단 입력 바 ──
          _buildInputBar(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(_ChatMessage message) {
    final isUser = message.isUser;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment:
            isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // 발신자 라벨
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text(
              isUser ? '나' : '도우미',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: HiBuddyColors.textMuted,
              ),
            ),
          ),

          // 메시지 버블
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.78,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: isUser ? HiBuddyColors.primary : Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(18),
                topRight: const Radius.circular(18),
                bottomLeft: Radius.circular(isUser ? 18 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 18),
              ),
              border: isUser
                  ? null
                  : Border.all(color: HiBuddyColors.border),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withAlpha(10),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Text(
              message.text,
              style: TextStyle(
                fontSize: 17,
                height: 1.5,
                color: isUser ? Colors.white : HiBuddyColors.text,
              ),
            ),
          ),

          // 에이전트 메시지: TTS 재생 버튼
          if (!isUser)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: InkWell(
                onTap: () => TtsService.speak(message.text),
                borderRadius: BorderRadius.circular(20),
                child: const Padding(
                  padding: EdgeInsets.all(4),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.volume_up, size: 18, color: HiBuddyColors.textMuted),
                      SizedBox(width: 4),
                      Text(
                        '다시 듣기',
                        style: TextStyle(fontSize: 13, color: HiBuddyColors.textMuted),
                      ),
                    ],
                  ),
                ),
              ),
            ),

          // 유튜브 버튼
          if (!isUser && message.youtubeQuery != null)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => YouTubeScreen(
                          searchQuery: message.youtubeQuery,
                          title: '유튜브 보기',
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.play_circle_outline, size: 22),
                  label: const Text(
                    '유튜브 보기',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                  ),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFFFF0000),
                    side: const BorderSide(color: Color(0xFFFF0000)),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
              ),
            ),

          // 액션 버튼들
          if (!isUser && message.actions.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Wrap(
                spacing: 8,
                runSpacing: 8,
                children: message.actions.map((action) {
                  return SizedBox(
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () => _handleAction(action),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: HiBuddyColors.primaryBg,
                        foregroundColor: HiBuddyColors.primary,
                        elevation: 0,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(24),
                          side: const BorderSide(color: HiBuddyColors.primaryLight),
                        ),
                      ),
                      child: Text(
                        action.label,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLoadingBubble() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.only(bottom: 4),
            child: Text(
              '도우미',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: HiBuddyColors.textMuted,
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(18),
                topRight: Radius.circular(18),
                bottomLeft: Radius.circular(4),
                bottomRight: Radius.circular(18),
              ),
              border: Border.all(color: HiBuddyColors.border),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: HiBuddyColors.primary,
                  ),
                ),
                SizedBox(width: 12),
                Text(
                  '생각하고 있어요...',
                  style: TextStyle(
                    fontSize: 16,
                    color: HiBuddyColors.textMuted,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputBar() {
    return Container(
      padding: EdgeInsets.only(
        left: 12,
        right: 8,
        top: 10,
        bottom: MediaQuery.of(context).padding.bottom + 10,
      ),
      decoration: BoxDecoration(
        color: Colors.white,
        border: const Border(
          top: BorderSide(color: HiBuddyColors.border),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(8),
            blurRadius: 8,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          // 텍스트 입력
          Expanded(
            child: TextField(
              controller: _textController,
              focusNode: _focusNode,
              style: const TextStyle(fontSize: 17),
              decoration: InputDecoration(
                hintText: '여기에 입력하세요...',
                hintStyle: const TextStyle(
                  fontSize: 16,
                  color: HiBuddyColors.textMuted,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: HiBuddyColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: HiBuddyColors.border),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                  borderSide: const BorderSide(color: HiBuddyColors.primary, width: 2),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                filled: true,
                fillColor: HiBuddyColors.bg,
              ),
              textInputAction: TextInputAction.send,
              onSubmitted: _sendMessage,
              maxLines: 1,
            ),
          ),
          const SizedBox(width: 6),

          // TTS/마이크 버튼
          SizedBox(
            width: 48,
            height: 48,
            child: IconButton(
              onPressed: () {
                // 마지막 에이전트 메시지를 다시 읽어줌
                final lastAgent = _messages.lastWhere(
                  (m) => !m.isUser,
                  orElse: () => const _ChatMessage(text: '', isUser: false),
                );
                if (lastAgent.text.isNotEmpty) {
                  TtsService.speak(lastAgent.text);
                }
              },
              icon: const Icon(Icons.volume_up),
              color: HiBuddyColors.primary,
              tooltip: '마지막 답변 듣기',
            ),
          ),

          // 전송 버튼
          SizedBox(
            width: 48,
            height: 48,
            child: IconButton(
              onPressed: () => _sendMessage(_textController.text),
              icon: const Icon(Icons.send_rounded),
              color: Colors.white,
              style: IconButton.styleFrom(
                backgroundColor: HiBuddyColors.primary,
                shape: const CircleBorder(),
              ),
              tooltip: '보내기',
            ),
          ),
        ],
      ),
    );
  }
}
