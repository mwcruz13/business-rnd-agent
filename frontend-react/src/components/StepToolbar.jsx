import { useRef, useContext } from 'react';
import { Box, Button, Text, ResponsiveContext } from 'grommet';
import { Download, Upload } from 'grommet-icons';
import { stepFieldsToYaml, yamlToStepFields, stepYamlFilename } from '../utils/yamlStepFields.js';

/**
 * Shared toolbar for every step card.
 * Renders the step title and Download / Upload YAML buttons.
 */
const StepToolbar = ({ stepIndex, stepLabel, runState, sessionId, onImport }) => {
  const fileInputRef = useRef(null);
  const size = useContext(ResponsiveContext);
  const isSmall = size === 'small';

  const handleDownload = () => {
    const yamlStr = stepFieldsToYaml(stepIndex, runState);
    if (!yamlStr) return;

    const blob = new Blob([yamlStr], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = stepYamlFilename(stepIndex, sessionId);
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const parsed = yamlToStepFields(stepIndex, e.target.result);
        if (Object.keys(parsed).length > 0) {
          onImport(parsed);
        }
      } catch (err) {
        console.error('YAML parse error:', err);
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-uploaded
    event.target.value = '';
  };

  return (
    <Box
      direction={isSmall ? 'column' : 'row'}
      align={isSmall ? 'start' : 'center'}
      justify="between"
      pad={{ horizontal: isSmall ? 'small' : 'medium', vertical: 'small' }}
      border={{ side: 'bottom', color: 'border' }}
      flex={false}
      gap={isSmall ? 'small' : undefined}
    >
      <Text weight="bold" size={isSmall ? 'small' : 'medium'}>
        Step {stepIndex + 1}: {stepLabel}
      </Text>

      <Box direction="row" gap="small">
        <Button
          icon={<Download size="small" />}
          label={isSmall ? undefined : 'Download'}
          size="small"
          onClick={handleDownload}
          tip="Download step content as YAML"
        />
        <Button
          icon={<Upload size="small" />}
          label={isSmall ? undefined : 'Upload'}
          size="small"
          onClick={handleUploadClick}
          tip="Upload YAML to populate step fields"
        />
        <input
          ref={fileInputRef}
          type="file"
          accept=".yaml,.yml"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </Box>
    </Box>
  );
};

export default StepToolbar;
