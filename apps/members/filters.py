# filters.py
from django_filters.rest_framework import DjangoFilterBackend
from .models import Section

class HierarchicalSectionFilterBackend(DjangoFilterBackend):
    """
    A filter backend that handles section filtering hierarchically.
    When filtering by section, it includes all elements from subsections too.
    """
    
    def filter_queryset(self, request, queryset, view):
        # Apply standard filtering first for everything except section
        filtered_queryset = super().filter_queryset(request, queryset, view)
        
        # Check if filtering by section
        section_id = request.query_params.get('section')
        if not section_id:
            return filtered_queryset
        
        # Get the current user from the request
        user = request.user
        
        # Get all section IDs including subsections
        section_ids = [section_id]
        
        def get_subsection_ids(parent_id):
            subsection_ids = []
            subsections = Section.objects.filter(parent_id=parent_id, user=user)
            for sub in subsections:
                subsection_ids.append(sub.id)
                subsection_ids.extend(get_subsection_ids(sub.id))
            return subsection_ids
        
        # Add all subsections to the filter
        section_ids.extend(get_subsection_ids(section_id))
        
        # Apply our section filter
        result_queryset = queryset.model.objects.filter(user=user, section__in=section_ids)
        
        # Apply any other filters that were in the query parameters
        # This part needs special handling for boolean fields
        for name, value in request.query_params.items():
            if name != 'section' and hasattr(view, 'filterset_fields') and name in view.filterset_fields:
                # Special handling for boolean fields
                if name == 'is_completed' or name == 'is_archived' or name == 'is_favorite':
                    # Convert string to boolean
                    if value.lower() == 'true':
                        bool_value = True
                    elif value.lower() == 'false':
                        bool_value = False
                    else:
                        continue  # Skip invalid boolean values
                    
                    filter_kwargs = {name: bool_value}
                else:
                    filter_kwargs = {name: value}
                
                result_queryset = result_queryset.filter(**filter_kwargs)
        
        # If the queryset has a specific type filter (e.g., for TodoViewSet),
        # make sure to apply it to our new queryset
        if hasattr(queryset, 'query') and hasattr(queryset.model, 'type'):
            # Inspect the original queryset to see if it's filtering by type
            if hasattr(view, 'get_queryset'):
                original_queryset = view.get_queryset()
                if hasattr(original_queryset, 'query'):
                    # Get the base queryset type if it exists
                    try:
                        first_item = original_queryset.first()
                        if first_item and hasattr(first_item, 'type'):
                            result_queryset = result_queryset.filter(type=first_item.type)
                    except:
                        pass
        
        return result_queryset



# # filters.py
# from django_filters.rest_framework import DjangoFilterBackend
# from .models import Section

# class HierarchicalSectionFilterBackend(DjangoFilterBackend):
#     """
#     A filter backend that handles section filtering hierarchically.
#     When filtering by section, it includes all elements from subsections too.
#     """
    
#     def filter_queryset(self, request, queryset, view):
#         # Apply standard filtering first (this will handle all filters except our custom section filter)
#         filtered_queryset = super().filter_queryset(request, queryset, view)
        
#         # Check if filtering by section
#         section_id = request.query_params.get('section')
#         if not section_id:
#             return filtered_queryset
        
#         # Get the current user from the request
#         user = request.user
        
#         # Get all section IDs including subsections
#         section_ids = [section_id]
        
#         def get_subsection_ids(parent_id):
#             subsection_ids = []
#             subsections = Section.objects.filter(parent_id=parent_id, user=user)
#             for sub in subsections:
#                 subsection_ids.append(sub.id)
#                 subsection_ids.extend(get_subsection_ids(sub.id))
#             return subsection_ids
        
#         # Add all subsections to the filter
#         section_ids.extend(get_subsection_ids(section_id))
        
#         # Create a new queryset with our section filter
#         # Start with the base queryset that has user filtering already applied
#         base_queryset = queryset.model.objects.filter(user=user)
        
#         # Apply type filter if this is a specialized viewset (like TodoViewSet)
#         if hasattr(view, 'get_queryset'):
#             # Check if the viewset has a type filter in its get_queryset method
#             viewset_queryset = view.get_queryset()
#             if hasattr(viewset_queryset, 'query'):
#                 # Try to extract type filter if it exists
#                 base_queryset = base_queryset.filter(type=viewset_queryset.first().type if viewset_queryset.exists() else None)
        
#         # Apply our hierarchical section filter
#         result_queryset = base_queryset.filter(section__in=section_ids)
        
#         # Apply any other filters that were applied to the original filtered_queryset
#         # This is a simple approach that works for most cases
#         for name, value in request.query_params.items():
#             if name != 'section' and hasattr(view, 'filterset_fields') and name in view.filterset_fields:
#                 filter_kwargs = {name: value}
#                 result_queryset = result_queryset.filter(**filter_kwargs)
        
#         return result_queryset