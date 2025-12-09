import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  RadioGroup,
  FormControlLabel,
  Radio,
  Card,
  CardContent,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import PaymentIcon from '@mui/icons-material/Payment';

const PaymentDialog = ({ open, onClose, payment, onPaymentSuccess }) => {
  const [paymentMethod, setPaymentMethod] = useState('card');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  const handlePayment = async () => {
    setProcessing(true);
    setError('');

    try {
      // Simulate payment processing delay
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Call the payment service
      await onPaymentSuccess(payment.payment_id, paymentMethod);

      // Close dialog on success
      onClose();
    } catch (err) {
      setError(err.message || 'Ошибка обработки платежа');
    } finally {
      setProcessing(false);
    }
  };

  const getPaymentMethodIcon = (method) => {
    switch (method) {
      case 'card':
        return <CreditCardIcon />;
      case 'cash':
        return <AccountBalanceIcon />;
      case 'online':
        return <PaymentIcon />;
      default:
        return <PaymentIcon />;
    }
  };

  const getPaymentMethodName = (method) => {
    switch (method) {
      case 'card':
        return 'Банковская карта';
      case 'cash':
        return 'Наличные при въезде';
      case 'online':
        return 'Онлайн-перевод';
      default:
        return method;
    }
  };

  if (!payment) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PaymentIcon color="primary" />
          <span>Оплата бронирования</span>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Payment Details */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Детали платежа
            </Typography>

            {payment.spot && payment.zone && (
              <>
                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Парковочное место
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    Место {payment.spot.spot_number}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {payment.zone.name} • {payment.zone.address}
                  </Typography>
                </Box>

                {payment.booking && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Период бронирования
                    </Typography>
                    <Typography variant="body2">
                      {new Date(payment.booking.start_time).toLocaleString('ru-RU', {
                        day: '2-digit',
                        month: 'long',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Typography>
                    <Typography variant="body2">
                      {new Date(payment.booking.end_time).toLocaleString('ru-RU', {
                        day: '2-digit',
                        month: 'long',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </Typography>
                  </Box>
                )}
              </>
            )}

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6">
                К оплате:
              </Typography>
              <Typography variant="h5" color="primary" fontWeight="bold">
                {parseFloat(payment.amount).toFixed(2)} ₽
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Payment Method Selection */}
        <Typography variant="h6" gutterBottom>
          Способ оплаты
        </Typography>

        <RadioGroup
          value={paymentMethod}
          onChange={(e) => setPaymentMethod(e.target.value)}
        >
          <Card
            variant="outlined"
            sx={{
              mb: 1,
              cursor: 'pointer',
              border: paymentMethod === 'card' ? 2 : 1,
              borderColor: paymentMethod === 'card' ? 'primary.main' : 'divider'
            }}
            onClick={() => setPaymentMethod('card')}
          >
            <CardContent sx={{ py: 1.5 }}>
              <FormControlLabel
                value="card"
                control={<Radio />}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CreditCardIcon color={paymentMethod === 'card' ? 'primary' : 'action'} />
                    <Box>
                      <Typography variant="body1">
                        {getPaymentMethodName('card')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Visa, Mastercard, МИР
                      </Typography>
                    </Box>
                  </Box>
                }
                sx={{ m: 0, width: '100%' }}
              />
            </CardContent>
          </Card>

          <Card
            variant="outlined"
            sx={{
              mb: 1,
              cursor: 'pointer',
              border: paymentMethod === 'online' ? 2 : 1,
              borderColor: paymentMethod === 'online' ? 'primary.main' : 'divider'
            }}
            onClick={() => setPaymentMethod('online')}
          >
            <CardContent sx={{ py: 1.5 }}>
              <FormControlLabel
                value="online"
                control={<Radio />}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PaymentIcon color={paymentMethod === 'online' ? 'primary' : 'action'} />
                    <Box>
                      <Typography variant="body1">
                        {getPaymentMethodName('online')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        СБП, Яндекс.Деньги, QIWI
                      </Typography>
                    </Box>
                  </Box>
                }
                sx={{ m: 0, width: '100%' }}
              />
            </CardContent>
          </Card>

          <Card
            variant="outlined"
            sx={{
              cursor: 'pointer',
              border: paymentMethod === 'cash' ? 2 : 1,
              borderColor: paymentMethod === 'cash' ? 'primary.main' : 'divider'
            }}
            onClick={() => setPaymentMethod('cash')}
          >
            <CardContent sx={{ py: 1.5 }}>
              <FormControlLabel
                value="cash"
                control={<Radio />}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <AccountBalanceIcon color={paymentMethod === 'cash' ? 'primary' : 'action'} />
                    <Box>
                      <Typography variant="body1">
                        {getPaymentMethodName('cash')}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Оплата на парковке
                      </Typography>
                    </Box>
                  </Box>
                }
                sx={{ m: 0, width: '100%' }}
              />
            </CardContent>
          </Card>
        </RadioGroup>

        <Alert severity="info" sx={{ mt: 2 }}>
          Это демо-режим. Оплата будет имитирована без реального списания средств.
        </Alert>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button onClick={onClose} disabled={processing}>
          Отмена
        </Button>
        <Button
          onClick={handlePayment}
          variant="contained"
          size="large"
          disabled={processing}
          startIcon={processing ? <CircularProgress size={20} /> : getPaymentMethodIcon(paymentMethod)}
        >
          {processing ? 'Обработка...' : `Оплатить ${parseFloat(payment.amount).toFixed(2)} ₽`}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PaymentDialog;
