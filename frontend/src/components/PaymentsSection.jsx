import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  PaymentOutlined as PaymentIcon,
  CheckCircleOutline as CheckIcon,
  ErrorOutline as ErrorIcon,
} from '@mui/icons-material';
import parkingService from '../services/parkingService';

const PaymentsSection = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingPayment, setProcessingPayment] = useState(null);

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const data = await parkingService.getPayments();
      setPayments(data);
    } catch (err) {
      setError('Ошибка загрузки платежей');
      console.error('Failed to load payments:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async (paymentId) => {
    try {
      setProcessingPayment(paymentId);
      setError('');

      // Обновляем статус на completed, backend обработает через mock service
      await parkingService.updatePaymentStatus(paymentId, {
        status: 'completed',
      });

      // Перезагружаем платежи
      await loadPayments();
      setProcessingPayment(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка обработки платежа');
      setProcessingPayment(null);
    }
  };

  const getStatusChip = (status) => {
    const statusConfig = {
      pending: { label: 'Ожидает оплаты', color: 'warning', icon: <PaymentIcon /> },
      completed: { label: 'Оплачено', color: 'success', icon: <CheckIcon /> },
      failed: { label: 'Отклонено', color: 'error', icon: <ErrorIcon /> },
      refunded: { label: 'Возврат', color: 'info', icon: <ErrorIcon /> },
    };

    const config = statusConfig[status] || statusConfig.pending;

    return (
      <Chip
        label={config.label}
        color={config.color}
        size="small"
        icon={config.icon}
      />
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Мои платежи
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  return (
    <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        Мои платежи
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {payments.length === 0 ? (
        <Typography color="text.secondary">Платежей пока нет</Typography>
      ) : (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Дата</TableCell>
                <TableCell align="right">Сумма</TableCell>
                <TableCell>Способ оплаты</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>ID транзакции</TableCell>
                <TableCell align="center">Действие</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {payments.map((payment) => (
                <TableRow key={payment.payment_id}>
                  <TableCell>{formatDate(payment.created_at)}</TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="bold">
                      {parseFloat(payment.amount).toFixed(2)} ₽
                    </Typography>
                  </TableCell>
                  <TableCell>{payment.payment_method}</TableCell>
                  <TableCell>{getStatusChip(payment.status)}</TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {payment.transaction_id || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    {payment.status === 'pending' && (
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handlePayment(payment.payment_id)}
                        disabled={processingPayment === payment.payment_id}
                        startIcon={processingPayment === payment.payment_id ? <CircularProgress size={16} /> : <PaymentIcon />}
                      >
                        {processingPayment === payment.payment_id ? 'Обработка...' : 'Оплатить'}
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default PaymentsSection;
