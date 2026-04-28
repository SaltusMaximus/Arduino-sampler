clc;
clear;
close all;

%% PARAMETERS
filename = 'capacitor_8bit_raw.bin';
captureTime = 17.0;   % seconds (same as Arduino)
Vref = 5.0;

%% LOAD RAW DATA
fid = fopen(filename, 'rb');
raw = fread(fid, inf, 'uint8=>uint8');
fclose(fid);

N = length(raw);

%% RECONSTRUCT TIME + VOLTAGE
fs = N / captureTime;           % estimated sampling rate
t = (0:N-1) / fs;              % time vector
v = double(raw) * Vref / 255.0;

fprintf('Samples: %d\n', N);
fprintf('Estimated sampling rate: %.2f samples/s\n', fs);

%% PLOT RAW DATA
figure;
plot(t, v, 'LineWidth', 1.2);
grid on;
xlabel('Time (s)');
ylabel('Voltage (V)');
title('Capacitor Voltage vs Time');

%% ===== TIME CONSTANT ESTIMATION =====
% Choose region automatically (avoid zeros / noise floor)
threshold = 0.05 * max(v);
idx = v > threshold;

t_fit = t(idx);
v_fit = v(idx);

% Decide if it's charging or discharging
if v_fit(end) > v_fit(1)
    % Charging: V = Vf(1 - exp(-t/tau))
    fprintf('Detected: CHARGING curve\n');

    ft = fittype('a*(1 - exp(-x/tau))', ...
        'independent', 'x', ...
        'coefficients', {'a','tau'});

    model = fit(t_fit', v_fit', ft);

    tau = model.tau;
    Vf = model.a;

    fprintf('Final voltage Vf = %.4f V\n', Vf);

else
    % Discharging: V = V0 * exp(-t/tau)
    fprintf('Detected: DISCHARGING curve\n');

    ft = fittype('a*exp(-x/tau)', ...
        'independent', 'x', ...
        'coefficients', {'a','tau'});

    model = fit(t_fit', v_fit', ft);

    tau = model.tau;
    V0 = model.a;

    fprintf('Initial voltage V0 = %.4f V\n', V0);
end

fprintf('Estimated tau = %.6f seconds\n', tau);

%% PLOT FIT OVER DATA
figure;
plot(t, v, 'b');
hold on;
plot(model, t_fit, v_fit);
grid on;

xlabel('Time (s)');
ylabel('Voltage (V)');
title('Capacitor Curve + Exponential Fit');

legend('Raw Data', 'Fit');