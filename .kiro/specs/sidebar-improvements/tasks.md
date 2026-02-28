# Implementation Plan

- [x] 1. Create sidebar state management store
  - Create `src/stores/sidebar-store.ts` with Zustand
  - Implement state for AppSidebar, IdeSidebar, and ConnectorsPanel open/closed
  - Add toggle functions for all three sidebars
  - Implement localStorage persistence with debouncing
  - Set default states (all open)
  - _Requirements: 2.2, 2.4, 2.5_

- [ ]* 1.1 Write property test for sidebar state persistence
  - **Property 1: Sidebar state persistence**
  - **Validates: Requirements 2.4**

- [ ]* 1.2 Write property test for independent sidebar toggles
  - **Property 2: Independent sidebar toggles**
  - **Validates: Requirements 2.2**

- [ ] 1.3 Update sidebar store to include ConnectorsPanel state
  - Add `connectorsPanelOpen` state to sidebar store
  - Add `toggleConnectorsPanel` and `setConnectorsPanelOpen` actions
  - Update localStorage persistence to include ConnectorsPanel state
  - Set default state for ConnectorsPanel (open)
  - _Requirements: 2.5, 6.5_

- [x] 2. Create shared sidebar components
  - Create `src/components/sidebar/` directory
  - Implement `SidebarHeader` component with consistent styling
  - Implement `SidebarSection` component for section labels
  - Implement `SidebarItem` component for list items
  - Implement `SidebarToggle` button component
  - Use CSS variables for all styling
  - Add proper TypeScript interfaces
  - _Requirements: 1.1, 1.2_

- [ ]* 2.1 Write unit tests for shared sidebar components
  - Test SidebarHeader rendering and props
  - Test SidebarSection rendering
  - Test SidebarItem interactive states
  - Test SidebarToggle button functionality
  - _Requirements: 1.1, 1.2_

- [ ]* 2.2 Write property test for consistent border styling
  - **Property 6: Consistent border styling**
  - **Validates: Requirements 1.2**

- [x] 3. Refactor AppSidebar component
  - Update `src/components/layout/app-sidebar.tsx`
  - Replace custom header with SidebarHeader component
  - Replace section labels with SidebarSection component
  - Replace conversation items with SidebarItem component
  - Add SidebarToggle button to header
  - Integrate with sidebar store for collapse state
  - Ensure all styling uses CSS variables
  - Maintain existing conversation functionality
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [ ]* 3.1 Write unit tests for refactored AppSidebar
  - Test toggle functionality
  - Test conversation list rendering
  - Test new chat button
  - Test delete conversation
  - _Requirements: 2.1, 2.2_

- [x] 4. Refactor IdeSidebar component
  - Update `src/components/ide/ide-sidebar.tsx`
  - Replace custom header with SidebarHeader component
  - Replace section labels with SidebarSection component
  - Add SidebarToggle button to header
  - Integrate with sidebar store for collapse state
  - Ensure all styling uses CSS variables
  - Maintain existing file tree functionality
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [ ]* 4.1 Write unit tests for refactored IdeSidebar
  - Test toggle functionality
  - Test file tree rendering
  - Test create file/folder buttons
  - _Requirements: 2.1, 2.2_

- [x] 5. Implement file creation validation
  - Update file creation logic in IDE store
  - Add validation for invalid characters (/, \, :, *, ?, ", <, >, |)
  - Add validation for empty names
  - Add validation for name length
  - Return descriptive error messages
  - _Requirements: 3.4_

- [ ]* 5.1 Write property test for file creation validation
  - **Property 4: File creation validation**
  - **Validates: Requirements 3.4**

- [x] 6. Fix file creation and tree update
  - Update `src/stores/ide-store.ts` createNode function
  - Ensure file tree refreshes immediately after creation
  - Add optimistic updates for better UX
  - Handle creation errors gracefully
  - Display toast notifications for success/error
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [ ]* 6.1 Write property test for file tree update
  - **Property 5: File tree update after creation**
  - **Validates: Requirements 3.5**

- [ ]* 6.2 Write unit tests for file creation
  - Test successful file creation
  - Test successful folder creation
  - Test error handling
  - Test toast notifications
  - _Requirements: 3.1, 3.2, 3.3, 3.5_

- [x] 7. Refactor IdePage to include dual sidebars
  - Update `src/pages/ide-page.tsx`
  - Add AppSidebar to the layout
  - Implement transition wrappers for both sidebars
  - Add conditional rendering based on sidebar store state
  - Ensure proper layout with both sidebars
  - Adjust main content area to use remaining space
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 7.1 Write property test for layout space utilization
  - **Property 3: Layout space utilization**
  - **Validates: Requirements 2.3**

- [ ]* 7.2 Write unit tests for IdePage layout
  - Test dual sidebar rendering
  - Test sidebar visibility based on state
  - Test main content area sizing
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 8. Implement navigation preservation
  - Ensure clicking conversations in AppSidebar on IDE page navigates to Chat page
  - Verify conversation ID is passed correctly
  - Test navigation with different conversation IDs
  - _Requirements: 4.4_

- [ ]* 8.1 Write property test for navigation preservation
  - **Property 7: Navigation preservation**
  - **Validates: Requirements 4.4**

- [ ] 9. Refactor ConnectorsPanel for consistency
  - Update `src/components/drive/connectors-panel.tsx`
  - Replace `isPanelOpen` from AuthStore with sidebar store state
  - Update header height from `h-[57px]` to `h-[60px]`
  - Change header background from `bg-background` to `bg-sidebar`
  - Add SidebarToggle button to header
  - Ensure all styling uses CSS variables
  - Update border to use `border-sidebar-border`
  - Maintain existing Google Drive functionality
  - _Requirements: 1.2, 1.4, 6.1, 6.2, 6.3, 6.4_

- [ ]* 9.1 Write property test for ConnectorsPanel styling consistency
  - **Property 8: ConnectorsPanel styling consistency**
  - **Validates: Requirements 6.1, 6.2, 6.3**

- [ ]* 9.2 Write unit tests for refactored ConnectorsPanel
  - Test toggle functionality
  - Test Google Drive connection flow
  - Test file browsing
  - Test disconnect functionality
  - _Requirements: 2.5, 6.5_

- [ ] 10. Refactor AuthStore to remove isPanelOpen
  - Remove `isPanelOpen` state from `src/stores/auth-store.ts`
  - Remove `togglePanel` action
  - Update any components using `isPanelOpen` to use sidebar store instead
  - Maintain all other AuthStore functionality
  - _Requirements: 6.1_

- [ ] 11. Update ChatPage to use sidebar store for ConnectorsPanel
  - Update `src/pages/chat-page.tsx`
  - Add transition wrapper for ConnectorsPanel
  - Use sidebar store state for conditional rendering
  - Ensure smooth collapse/expand animation
  - _Requirements: 2.5, 6.5_

- [ ]* 11.1 Write property test for ConnectorsPanel toggle behavior
  - **Property 9: ConnectorsPanel toggle behavior**
  - **Validates: Requirements 2.5, 6.5**

- [ ] 12. Add CSS transitions and animations
  - Update `src/index.css` with sidebar transition styles
  - Add smooth collapse/expand animations for all sidebars (left and right)
  - Use GPU-accelerated properties (transform, opacity)
  - Set transition duration to 200ms
  - Add ease-in-out easing
  - _Requirements: 2.1, 2.5_

- [ ] 13. Implement keyboard shortcuts
  - Add global keyboard listener for Ctrl+B (Cmd+B on Mac)
  - Add global keyboard listener for Ctrl+Shift+E (Cmd+Shift+E on Mac)
  - Add global keyboard listener for Ctrl+Shift+D (Cmd+Shift+D on Mac) for ConnectorsPanel
  - Toggle AppSidebar with Ctrl+B
  - Toggle IdeSidebar with Ctrl+Shift+E
  - Toggle ConnectorsPanel with Ctrl+Shift+D
  - Prevent default browser behavior
  - Add keyboard shortcut hints to UI (optional)
  - _Requirements: 2.1, 2.5_

- [ ]* 13.1 Write unit tests for keyboard shortcuts
  - Test Ctrl+B toggles AppSidebar
  - Test Ctrl+Shift+E toggles IdeSidebar
  - Test Ctrl+Shift+D toggles ConnectorsPanel
  - Test keyboard shortcuts work on both pages
  - _Requirements: 2.1, 2.5_

- [ ] 14. Add ARIA attributes and accessibility
  - Add aria-expanded to toggle buttons (including ConnectorsPanel)
  - Add aria-controls linking buttons to sidebars
  - Add aria-label to icon-only buttons
  - Add role="navigation" to sidebar containers
  - Add role="list" and role="listitem" to item lists
  - Ensure focus indicators are visible
  - Test with keyboard navigation
  - _Requirements: 5.3_

- [ ]* 14.1 Write accessibility tests
  - Test ARIA attributes are present
  - Test keyboard navigation works
  - Test focus management
  - _Requirements: 5.3_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Create design system documentation
  - Create `DESIGN_SYSTEM.md` in project root
  - Document all CSS variables and their usage
  - Document spacing scale
  - Document typography scale
  - Document component patterns with examples
  - Document interaction patterns
  - Document animation guidelines
  - Document accessibility standards
  - _Requirements: 1.1, 1.2_

- [ ] 17. Perform visual consistency audit
  - Compare AppSidebar, IdeSidebar, and ConnectorsPanel side-by-side
  - Verify all colors use CSS variables
  - Verify spacing is consistent
  - Verify typography is consistent
  - Verify borders are consistent
  - Verify interactive states are consistent
  - Verify icons are consistent
  - Take screenshots for documentation
  - _Requirements: 1.1, 1.2, 1.3, 6.1, 6.2, 6.3, 6.4_

- [x] 18. Remove visual clutter from AppSidebar
  - Remove "WordPress API" and "Groq AI" status indicators from footer
  - Update AppSidebar header border height to match other sidebars (h-[60px])
  - Ensure consistent border styling across all sidebar sections
  - _Requirements: 7.1, 7.2, 7.4_

- [x] 19. Update ConnectorsPanel toggle icon
  - Replace PanelRight icon with X (close) icon in header
  - Ensure icon size matches other sidebar toggle buttons
  - Update aria-label to reflect close action
  - _Requirements: 7.3_

- [ ] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
