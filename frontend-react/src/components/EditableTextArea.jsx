import { useState, useEffect, useRef } from 'react';
import { TextArea } from 'grommet';

/**
 * A controlled TextArea wrapper that maintains local state to prevent
 * cursor-jump issues caused by parent re-renders.
 *
 * Keystrokes update local state immediately (keeping cursor stable) while
 * still propagating onChange to the parent.  External value changes (e.g.,
 * import, initial seed) are synced into local state automatically.
 */
const EditableTextArea = ({ value, onChange, ...rest }) => {
  const [localValue, setLocalValue] = useState(value ?? '');
  const isTyping = useRef(false);

  // Sync from parent only when the change did NOT originate from typing.
  useEffect(() => {
    if (!isTyping.current) {
      setLocalValue(value ?? '');
    }
    isTyping.current = false;
  }, [value]);

  return (
    <TextArea
      {...rest}
      value={localValue}
      onChange={(e) => {
        isTyping.current = true;
        setLocalValue(e.target.value);
        onChange?.(e);
      }}
    />
  );
};

export default EditableTextArea;
