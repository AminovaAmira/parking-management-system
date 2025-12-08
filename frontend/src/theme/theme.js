import { createTheme } from '@mui/material/styles';

// Темная автомобильная премиальная тема
const darkAutomotiveTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d4ff', // Cyan - ассоциируется с технологиями и автомобилями
      light: '#5dffff',
      dark: '#00a3cc',
      contrastText: '#000000',
    },
    secondary: {
      main: '#ff9100', // Оранжевый - акцентный цвет
      light: '#ffc246',
      dark: '#c56200',
      contrastText: '#000000',
    },
    error: {
      main: '#f44336',
      light: '#ff7961',
      dark: '#ba000d',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#0a0e27', // Очень темный синий
      paper: '#141b2d', // Темно-синий для карточек
    },
    text: {
      primary: '#ffffff',
      secondary: '#b3b3b3',
      disabled: '#666666',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3rem',
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '2rem',
      letterSpacing: '0em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.75rem',
      letterSpacing: '0.00735em',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.5rem',
      letterSpacing: '0em',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1.25rem',
      letterSpacing: '0.0075em',
    },
    subtitle1: {
      fontWeight: 500,
      fontSize: '1rem',
      letterSpacing: '0.00938em',
    },
    subtitle2: {
      fontWeight: 500,
      fontSize: '0.875rem',
      letterSpacing: '0.00714em',
    },
    body1: {
      fontSize: '1rem',
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      letterSpacing: '0.01071em',
    },
    button: {
      fontWeight: 600,
      fontSize: '0.875rem',
      letterSpacing: '0.02857em',
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 12, // Более скругленные углы
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(0, 212, 255, 0.1)',
    '0px 4px 8px rgba(0, 212, 255, 0.15)',
    '0px 6px 12px rgba(0, 212, 255, 0.2)',
    '0px 8px 16px rgba(0, 212, 255, 0.25)',
    '0px 10px 20px rgba(0, 212, 255, 0.3)',
    '0px 12px 24px rgba(0, 212, 255, 0.35)',
    '0px 14px 28px rgba(0, 212, 255, 0.4)',
    '0px 16px 32px rgba(0, 212, 255, 0.45)',
    '0px 18px 36px rgba(0, 212, 255, 0.5)',
    '0px 20px 40px rgba(0, 212, 255, 0.55)',
    '0px 22px 44px rgba(0, 212, 255, 0.6)',
    '0px 24px 48px rgba(0, 212, 255, 0.65)',
    '0px 26px 52px rgba(0, 212, 255, 0.7)',
    '0px 28px 56px rgba(0, 212, 255, 0.75)',
    '0px 30px 60px rgba(0, 212, 255, 0.8)',
    '0px 32px 64px rgba(0, 212, 255, 0.85)',
    '0px 34px 68px rgba(0, 212, 255, 0.9)',
    '0px 36px 72px rgba(0, 212, 255, 0.95)',
    '0px 38px 76px rgba(0, 212, 255, 1)',
    '0px 40px 80px rgba(0, 212, 255, 1)',
    '0px 42px 84px rgba(0, 212, 255, 1)',
    '0px 44px 88px rgba(0, 212, 255, 1)',
    '0px 46px 92px rgba(0, 212, 255, 1)',
    '0px 48px 96px rgba(0, 212, 255, 1)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
          padding: '10px 24px',
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0px 4px 12px rgba(0, 212, 255, 0.3)',
          },
        },
        contained: {
          background: 'linear-gradient(45deg, #00d4ff 30%, #00a3cc 90%)',
          '&:hover': {
            background: 'linear-gradient(45deg, #00a3cc 30%, #00d4ff 90%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#141b2d',
          border: '1px solid rgba(0, 212, 255, 0.1)',
        },
        elevation1: {
          boxShadow: '0px 4px 12px rgba(0, 0, 0, 0.5)',
        },
        elevation2: {
          boxShadow: '0px 6px 16px rgba(0, 0, 0, 0.6)',
        },
        elevation3: {
          boxShadow: '0px 8px 20px rgba(0, 0, 0, 0.7)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid rgba(0, 212, 255, 0.2)',
          transition: 'all 0.3s ease',
          '&:hover': {
            borderColor: 'rgba(0, 212, 255, 0.5)',
            boxShadow: '0px 8px 24px rgba(0, 212, 255, 0.2)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '& fieldset': {
              borderColor: 'rgba(0, 212, 255, 0.3)',
            },
            '&:hover fieldset': {
              borderColor: 'rgba(0, 212, 255, 0.5)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00d4ff',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#141b2d',
          backgroundImage: 'none',
          borderBottom: '1px solid rgba(0, 212, 255, 0.2)',
        },
      },
    },
  },
});

export default darkAutomotiveTheme;
