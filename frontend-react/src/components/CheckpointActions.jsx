import { useContext } from 'react';
import { Box, Button, Text, ResponsiveContext } from 'grommet';
import { Checkmark, Edit, Close } from 'grommet-icons';

/**
 * Approve / Edit / Cancel action bar shown when a checkpoint is active.
 */
const CheckpointActions = ({
  checkpointId,
  onApprove,
  onEdit,
  onCancel,
  isLoading,
  editMode,
}) => {
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  if (!checkpointId) return null;

  return (
    <Box
      direction={isSmall ? 'column' : 'row'}
      gap="small"
      pad="small"
      border={{ side: 'top', color: 'border' }}
      justify={isSmall ? 'center' : 'end'}
      align={isSmall ? 'stretch' : 'center'}
      background="background-front"
    >
      <Text size="small" color="text-weak" margin={isSmall ? undefined : { right: 'auto' }}>
        Checkpoint: <strong>{checkpointId}</strong>
      </Text>

      {editMode ? (
        <>
          <Button
            label="Cancel"
            icon={<Close size="small" />}
            onClick={onCancel}
            disabled={isLoading}
            secondary
          />
          <Button
            label="Save & Resume"
            icon={<Checkmark size="small" />}
            onClick={onApprove}
            disabled={isLoading}
            primary
          />
        </>
      ) : (
        <>
          <Button
            label="Edit"
            icon={<Edit size="small" />}
            onClick={onEdit}
            disabled={isLoading}
            secondary
          />
          <Button
            label="Approve"
            icon={<Checkmark size="small" />}
            onClick={onApprove}
            disabled={isLoading}
            primary
          />
        </>
      )}
    </Box>
  );
};

export default CheckpointActions;
