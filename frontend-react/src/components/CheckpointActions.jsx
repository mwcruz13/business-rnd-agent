import { Box, Button, Text } from 'grommet';
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
  if (!checkpointId) return null;

  return (
    <Box
      direction="row"
      wrap
      gap="small"
      pad="small"
      border={{ side: 'top', color: 'border' }}
      justify="end"
      align="center"
      background="background-front"
    >
      <Text size="small" color="text-weak" margin={{ right: 'auto' }}>
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
