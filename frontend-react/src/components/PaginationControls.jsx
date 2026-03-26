import { Box, Button, Text } from 'grommet';
import { Previous, Next } from 'grommet-icons';

/**
 * Prev / Next pagination for multi-page step content.
 */
const PaginationControls = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;

  return (
    <Box direction="row" align="center" justify="center" gap="small" pad="small">
      <Button
        icon={<Previous size="small" />}
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 0}
        tip="Previous page"
      />
      <Text size="small" color="text-weak">
        {page + 1} / {totalPages}
      </Text>
      <Button
        icon={<Next size="small" />}
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages - 1}
        tip="Next page"
      />
    </Box>
  );
};

export default PaginationControls;
