# Arcadia UI Style - Known Issues

## Theme System Issues

### 🔴 **Theme Submenu Not Visible**
**Status:** Under Investigation  
**Last Updated:** Oct 22, 2025

#### Symptoms
- Theme trigger button appears in account menu
- Console shows successful theme building logs
- Clicking "Theme" shows debug messages but no visible theme options
- Theme switching works if called manually via `window.ArcadiaTheme.applyTheme('dark')`

#### Current Debugging Status
✅ JavaScript loads correctly  
✅ Theme system initializes  
✅ SUBMENU elements found  
✅ Trigger click events fire  
✅ Theme items are built (console shows item creation)  
❌ Theme items not visible to user  

#### Suspected Causes
1. **CSS Visibility Issue**: Theme items may have no background/visible styling
2. **Submenu Positioning**: Theme submenu may be positioned off-screen
3. **Z-index Conflicts**: Theme submenu may be hidden behind other elements
4. **HTML Structure**: Race condition in DOM element creation

#### Debugging Commands
```javascript
// Check if theme items exist
document.querySelectorAll('.theme-item').length

// Check submenu visibility
getComputedStyle(document.getElementById('theme-submenu')).display

// Check submenu position
document.getElementById('theme-submenu').getBoundingClientRect()

// Manual theme application test
window.ArcadiaTheme.applyTheme('dark')
```

#### Investigation Steps Needed
1. Inspect generated HTML structure in browser dev tools
2. Check computed styles for `.theme-item` elements  
3. Verify_submenu positioning coordinates
4. Test with different CSS z-index values

---

## Other Known Issues

### ⚠️ **HTMX Integrity Check Failure**
**Message:** "Failed to find a valid digest in the 'integrity' attribute"  
**Impact:** HMX functionality may be blocked, but theme system doesn't depend on it  
**Status:** Not critical for theme functionality

---

## Previous Fixed Issues
✅ **CSS Variable Double Dashes** - Fixed (was generating `----bg` instead of `--bg`)  
✅ **Header Color Missing** - Fixed (restored dark blue gradient headers)  
✅ **Template Contamination** - Fixed (removed Lang project menu items)  
✅ **Database Contamination** - Fixed (cleared test app database)  

---

## Testing Checklist
- [ ] Theme items visible in submenu
- [ ] Clicking theme items switches themes  
- [ ] Theme swatches display correct colors
- [ ] Theme persistence across page reloads
- [ ] Both light and dark themes work correctly
- [ ] Header styling remains consistent

---

**For more information, check browser console logs and use the debugging commands above.**
