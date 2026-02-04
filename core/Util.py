import torchaudio
import torch
import random
import torch.nn.functional as F 
import soundfile as sf
import numpy as np
class Util:
    @staticmethod
    def open(audio_path: str):
        sig, sr = sf.read(audio_path, dtype='float32', always_2d=True)
        sig = torch.tensor(sig).T
        return (sig, sr)
    
    @staticmethod
    def rechannel(aud, new_channel):
        sig, sr = aud
        if sig.shape[0] == new_channel:
            return aud
        if new_channel == 1:
            # lấy 1 kênh tín hiệu
            resig = sig[:1, :]
        else:
            resig = torch.concat([sig, sig])
        return (resig, sr)
    
    @staticmethod
    def resample(aud, newsr):
        sig, sr = aud
        
        if newsr == sr:
            return aud
        num_channels = sig.shape[0]
        resig = torchaudio.transforms.Resample(sr, newsr)(sig[:1, :])
        if num_channels > 1:
            retwo = torchaudio.transforms.Resample(sr, newsr)(sig[1:,:])
            resig = torch.concat([resig, retwo])
        return (resig, newsr)
    
    @staticmethod
    def pad_trunc(aud, max_ms):
        sig, sr = aud
        num_rows, sig_len = sig.shape
        max_len = (sr // 1000) * max_ms
        
        if max_len < sig_len:
            sig = sig[:,:max_len] # cắt âm thanh
        elif max_len > sig_len:
            pad_beggin_len = random.randint(0, max_len - sig_len)
            pad_end_len = max_len - sig_len - pad_beggin_len
            
            pad_beggin = torch.zeros((num_rows, pad_beggin_len))
            pad_end = torch.zeros((num_rows, pad_end_len))
            sig = torch.cat((pad_beggin, sig, pad_end), dim=1)
        return (sig, sr)
    
    @staticmethod
    def time_shift(aud, shift_time_limit):
        sig, sr = aud
        _, sig_len = sig.shape
        shift_amt = int(random.random() * shift_time_limit * sig_len)
        return (sig.roll(shift_amt), sr)
    
    @staticmethod
    def spectrogram(aud, n_mels = 64, n_fft = 1024, hop_len = None):
        sig, sr = aud
        top_db = 80
        # spec has shape [channel, n_mels, time] where channel is mono, stereo
        spec = torchaudio.transforms.MelSpectrogram(sr, n_fft=n_fft, hop_length=hop_len, n_mels=n_mels)(sig)
        # convert to decibels
        spec = torchaudio.transforms.AmplitudeToDB(top_db=top_db)(spec)
        return spec
    
    @staticmethod
    def spectrogram_augment(spec, max_mask_pct=0.1, n_freq_mask=1, n_time_masks = 1):
        _, n_mels, n_steps = spec.shape
        mask_value = spec.mean()
        aug_spec = spec
        freq_mask_param = max_mask_pct * n_mels
        for _ in range(n_freq_mask):
            aug_spec = torchaudio.transforms.FrequencyMasking(freq_mask_param)(aug_spec, mask_value)
        time_mask_param = max_mask_pct * n_steps
        for _ in range(n_time_masks):
            aug_spec = torchaudio.transforms.TimeMasking(time_mask_param)(aug_spec, mask_value)
        return aug_spec
    
    @staticmethod
    def normalize_rms(waveform, target_rms=0.14, tolerance=0.02, eps = 1e-8):
        # chuẩn hóa rms với biến động ngẫu nhiên
        target = np.random.uniform(target_rms - tolerance, target_rms + tolerance)
        current_rms = np.sqrt(np.mean(np.square(waveform)))
        gain = target / (current_rms + eps)
        normalized = waveform * gain
        normalized = np.clip(normalized, -1.0, 1.0)
        return normalized, target
    
# chuẩn hóa số lượng kênh và tần số lấy mẫu
def pipe_normAudio(aud, channels = 2, sample_rate = 44100): 
    aud = Util.rechannel(aud=aud, new_channel=channels)
    aud = Util.resample(aud=aud, newsr=sample_rate)
    return aud # (waveform, sr)

# chuẩn hóa từ audio thành dạng có thể đưa vào model
def audio2inputmodel(aud, channels = 2, sr = 44100, duration = 2000, aug = False):
    reaud = Util.resample(aud=aud, newsr=sr)
    rechan = Util.rechannel(aud=reaud, new_channel=channels)
    waveform, sample_rate = rechan[0], rechan[1]
    waveform = waveform.detach().cpu().numpy()
    norm, _ = Util.normalize_rms(waveform=waveform)
    norm = torch.tensor(norm)
    aud = (norm, sample_rate)
    dur_aud = Util.pad_trunc(aud, duration)
    sgram = Util.spectrogram(dur_aud, n_mels=64, n_fft=1024, hop_len=None)
    if aug:
        sgram = Util.spectrogram_augment(sgram, max_mask_pct=0.1, n_freq_mask=1, n_time_masks=1)
    sgram = sgram.unsqueeze(0)
    target_size = sgram.shape[2]
    inputs = F.interpolate(
        sgram, 
        size=(target_size, target_size), 
        mode='bilinear',
        align_corners=False
    )
    inputs = (inputs - inputs.mean(dim=(1,2,3), keepdim=True)) / (inputs.std(dim=(1,2,3), keepdim=True) + 1e-6)
    return inputs

# cắt cửa sổ spectrogram thành các khúc trượt.
def sliding_windows(waveform, sample_rate, window_ms=200, hop_ms = 50, channels = 2):
    window_len = int(sample_rate * window_ms / 1000)
    hop_len = int(sample_rate * hop_ms / 1000)
    total_len = waveform.shape[1]
    
    windows = []
    start = 0
    
    while start < total_len:
        end = start + window_len
        segment = waveform[:, start:end]
        if segment.shape[1] < window_len:
            pad_len = window_len - segment.shape[1]
            pad = torch.zeros((channels, pad_len))
            segment = torch.cat((segment, pad), dim=1)
        
        windows.append(segment)
        start += hop_len
    return torch.stack(windows)