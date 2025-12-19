import 'package:flutter/material.dart';
import '../utils/constants.dart';

enum FilterType { all, active, completed }

/// Filter bar for controlling todo list display
class FilterBar extends StatefulWidget {
  final FilterType initialFilter;
  final ValueChanged<FilterType> onFilterChanged;

  const FilterBar({
    Key? key,
    this.initialFilter = FilterType.all,
    required this.onFilterChanged,
  }) : super(key: key);

  @override
  State<FilterBar> createState() => _FilterBarState();
}

class _FilterBarState extends State<FilterBar> {
  late FilterType _selectedFilter;

  @override
  void initState() {
    super.initState();
    _selectedFilter = widget.initialFilter;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      key: Key(WidgetKeys.filterBar),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _buildFilterButton(
            label: 'All',
            filter: FilterType.all,
            keyName: WidgetKeys.showAllButton,
          ),
          _buildFilterButton(
            label: 'Active',
            filter: FilterType.active,
            keyName: WidgetKeys.showActiveButton,
          ),
          _buildFilterButton(
            label: 'Completed',
            filter: FilterType.completed,
            keyName: WidgetKeys.showCompletedButton,
          ),
        ],
      ),
    );
  }

  Widget _buildFilterButton({
    required String label,
    required FilterType filter,
    required String keyName,
  }) {
    final isSelected = _selectedFilter == filter;

    return ElevatedButton(
      key: Key(keyName),
      onPressed: () {
        setState(() {
          _selectedFilter = filter;
        });
        widget.onFilterChanged(filter);
      },
      style: ElevatedButton.styleFrom(
        backgroundColor: isSelected ? Colors.blue : Colors.grey[300],
        foregroundColor: isSelected ? Colors.white : Colors.black,
        elevation: isSelected ? 4 : 0,
      ),
      child: Text(label),
    );
  }
}
