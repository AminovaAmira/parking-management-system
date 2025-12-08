import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  IconButton,
} from '@mui/material';
import {
  CloudUpload,
  CheckCircle,
  Error,
  Close,
} from '@mui/icons-material';
import parkingService from '../services/parkingService';

const OCRUpload = ({ onPlateRecognized }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type)) {
      setError('Неверный формат файла. Разрешены: JPG, PNG');
      return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('Файл слишком большой. Максимальный размер: 10 МБ');
      return;
    }

    setSelectedFile(file);
    setError('');
    setResult(null);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Выберите изображение');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await parkingService.recognizeLicensePlate(formData);

      if (response.success) {
        setResult({
          success: true,
          licensePlate: response.license_plate,
          rawText: response.raw_text,
        });

        // Call parent callback with recognized plate
        if (onPlateRecognized) {
          onPlateRecognized(response.license_plate);
        }
      } else {
        setError(response.message || 'Не удалось распознать номер');
        setResult({ success: false });
      }
    } catch (err) {
      setError(err.message || 'Ошибка распознавания номера');
      setResult({ success: false });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError('');
  };

  return (
    <Box sx={{ my: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        Распознать номер из фото
      </Typography>

      {/* File Input */}
      <input
        accept="image/jpeg,image/jpg,image/png"
        style={{ display: 'none' }}
        id="ocr-file-input"
        type="file"
        onChange={handleFileSelect}
      />

      {/* Upload Area */}
      {!preview ? (
        <label htmlFor="ocr-file-input">
          <Paper
            variant="outlined"
            sx={{
              p: 3,
              textAlign: 'center',
              cursor: 'pointer',
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="body2" color="text.secondary">
              Нажмите для выбора изображения
            </Typography>
            <Typography variant="caption" color="text.secondary">
              JPG, PNG (макс. 10 МБ)
            </Typography>
          </Paper>
        </label>
      ) : (
        <Paper variant="outlined" sx={{ p: 2, position: 'relative' }}>
          <IconButton
            size="small"
            sx={{ position: 'absolute', top: 8, right: 8 }}
            onClick={handleClear}
          >
            <Close />
          </IconButton>

          {/* Image Preview */}
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <img
              src={preview}
              alt="Preview"
              style={{
                maxWidth: '100%',
                maxHeight: '200px',
                borderRadius: '4px',
              }}
            />
          </Box>

          {/* Upload Button */}
          {!result && (
            <Button
              variant="contained"
              fullWidth
              onClick={handleUpload}
              disabled={loading}
              startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
            >
              {loading ? 'Распознавание...' : 'Распознать номер'}
            </Button>
          )}

          {/* Result */}
          {result && (
            <Box sx={{ mt: 2 }}>
              {result.success ? (
                <Alert
                  severity="success"
                  icon={<CheckCircle />}
                  action={
                    <Button size="small" onClick={handleClear}>
                      Загрузить другое
                    </Button>
                  }
                >
                  <Typography variant="body2">
                    Номер распознан: <strong>{result.licensePlate}</strong>
                  </Typography>
                  {result.rawText && result.rawText !== result.licensePlate && (
                    <Typography variant="caption" color="text.secondary">
                      Исходный текст: {result.rawText}
                    </Typography>
                  )}
                </Alert>
              ) : (
                <Alert
                  severity="error"
                  icon={<Error />}
                  action={
                    <Button size="small" onClick={handleClear}>
                      Попробовать снова
                    </Button>
                  }
                >
                  Не удалось распознать номер. Попробуйте другое фото или введите номер вручную.
                </Alert>
              )}
            </Box>
          )}
        </Paper>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
    </Box>
  );
};

export default OCRUpload;
