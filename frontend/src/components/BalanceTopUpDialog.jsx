import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Card,
  CardContent,
  Alert,
  CircularProgress,
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import parkingService from '../services/parkingService';

const BalanceTopUpDialog = ({ open, onClose, onSuccess }) => {
  const [amount, setAmount] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  const handleTopUp = async () => {
    setProcessing(true);
    setError('');

    try {
      const topUpAmount = parseFloat(amount);

      if (isNaN(topUpAmount) || topUpAmount <= 0) {
        setError('Введите корректную сумму');
        setProcessing(false);
        return;
      }

      if (topUpAmount > 100000) {
        setError('Максимальная сумма пополнения: 100,000 ₽');
        setProcessing(false);
        return;
      }

      // Simulate payment processing delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Call the balance service
      await parkingService.topUpBalance(topUpAmount);

      // Call success callback to refresh user data
      if (onSuccess) {
        await onSuccess();
      }

      // Reset form and close dialog
      setAmount('');
      onClose();
    } catch (err) {
      setError(err.message || 'Ошибка пополнения баланса');
    } finally {
      setProcessing(false);
    }
  };

  const handleAmountChange = (e) => {
    const value = e.target.value;
    // Only allow numbers and decimal point
    if (value === '' || /^\d*\.?\d*$/.test(value)) {
      setAmount(value);
    }
  };

  const quickAmounts = [100, 500, 1000, 5000];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AccountBalanceWalletIcon color="success" />
          <span>Пополнение баланса</span>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Введите сумму пополнения
            </Typography>

            <TextField
              fullWidth
              label="Сумма (₽)"
              value={amount}
              onChange={handleAmountChange}
              placeholder="0.00"
              sx={{ mb: 2 }}
              InputProps={{
                endAdornment: <Typography sx={{ color: 'text.secondary' }}>₽</Typography>,
              }}
            />

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Быстрый выбор:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {quickAmounts.map((quickAmount) => (
                <Button
                  key={quickAmount}
                  variant={amount === String(quickAmount) ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setAmount(String(quickAmount))}
                >
                  {quickAmount} ₽
                </Button>
              ))}
            </Box>
          </CardContent>
        </Card>

        <Alert severity="info" sx={{ mt: 2 }}>
          После пополнения баланс будет доступен для оплаты бронирований. Средства будут списаны автоматически при подтверждении въезда.
        </Alert>

        <Alert severity="warning" sx={{ mt: 1 }}>
          Это демо-режим. Пополнение будет имитировано без реального списания средств.
        </Alert>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={processing}>
          Отмена
        </Button>
        <Button
          onClick={handleTopUp}
          variant="contained"
          size="large"
          color="success"
          disabled={processing || !amount || parseFloat(amount) <= 0}
          startIcon={processing ? <CircularProgress size={20} /> : <AccountBalanceWalletIcon />}
        >
          {processing ? 'Обработка...' : `Пополнить${amount ? ` на ${parseFloat(amount).toFixed(2)} ₽` : ''}`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BalanceTopUpDialog;
