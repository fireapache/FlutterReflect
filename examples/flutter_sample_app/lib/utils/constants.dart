/// Widget keys for FlutterReflect tool targeting
class WidgetKeys {
  // Input fields
  static const String addTodoInput = 'addTodoInput';
  static const String searchInput = 'searchInput';

  // Buttons
  static const String addTodoButton = 'addTodoButton';
  static const String deleteButtonPrefix = 'deleteButton_';
  static const String clearAllButton = 'clearAllButton';
  static const String markAllCompleteButton = 'markAllCompleteButton';
  static const String statsButton = 'statsButton';
  static const String backButton = 'backButton';

  // Lists
  static const String todoListView = 'todoListView';
  static const String filteredListView = 'filteredListView';

  // Checkboxes
  static const String todoDonePrefix = 'todoDone_';

  // Text displays
  static const String statsWidget = 'statsWidget';
  static const String interactionLog = 'interactionLog';

  // Filter buttons
  static const String showAllButton = 'showAllButton';
  static const String showActiveButton = 'showActiveButton';
  static const String showCompletedButton = 'showCompletedButton';
  static const String filterBar = 'filterBar';

  // Screens
  static const String homeScreen = 'homeScreen';
  static const String statsScreen = 'statsScreen';
}

/// Messages for interaction feedback
class InteractionMessages {
  static String taskAdded(String taskName) => '✓ Task added: $taskName';
  static String taskDeleted(String taskName) => '✓ Task deleted: $taskName';
  static const String taskCompleted = '✓ Task marked complete';
  static const String taskUncompleted = '✓ Task marked incomplete';
  static const String listScrolled = '↻ Scrolled list';
  static const String tasksCleared = '✓ All tasks cleared';
  static const String allCompleted = '✓ All tasks completed';
  static String tasksFiltered(int count) => '🔍 Filtered: $count tasks shown';
  static String tasksSearched(String query) => '🔍 Search: "$query"';
  static const String navigated = '→ Navigated to stats';
  static const String returnedHome = '← Returned home';
}
