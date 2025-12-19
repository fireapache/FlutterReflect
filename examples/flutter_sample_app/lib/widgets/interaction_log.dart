import 'package:flutter/material.dart';
import '../utils/constants.dart';

/// Displays temporary interaction feedback messages
class InteractionLogWidget extends StatefulWidget {
  final String message;
  final Duration displayDuration;

  const InteractionLogWidget({
    Key? key,
    required this.message,
    this.displayDuration = const Duration(seconds: 2),
  }) : super(key: key);

  @override
  State<InteractionLogWidget> createState() => _InteractionLogWidgetState();
}

class _InteractionLogWidgetState extends State<InteractionLogWidget>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();

    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );

    _fadeAnimation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeIn),
    );

    // Fade in
    _animationController.forward().then((_) {
      // Wait then fade out
      Future.delayed(widget.displayDuration, () {
        if (mounted) {
          _animationController.reverse();
        }
      });
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _fadeAnimation,
      child: Container(
        key: Key(WidgetKeys.interactionLog),
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.green.withOpacity(0.9),
          borderRadius: BorderRadius.circular(8),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.2),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Text(
          widget.message,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}

/// Manages a queue of interaction messages
class InteractionFeedbackManager extends ChangeNotifier {
  final List<String> _messageQueue = [];
  String? _currentMessage;

  String? get currentMessage => _currentMessage;

  void addMessage(String message) {
    _messageQueue.add(message);
    _processQueue();
  }

  void _processQueue() {
    if (_currentMessage == null && _messageQueue.isNotEmpty) {
      _currentMessage = _messageQueue.removeAt(0);
      notifyListeners();

      // Clear message after it's displayed
      Future.delayed(const Duration(seconds: 2), () {
        _currentMessage = null;
        notifyListeners();
        _processQueue();
      });
    }
  }
}
