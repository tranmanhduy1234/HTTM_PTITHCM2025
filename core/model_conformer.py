import torch.nn as nn
# from torch.utils.tensorboard import SummaryWriter
# import math


class ConformerBlock(nn.Module):
    def __init__(self, dim, num_heads, mlp_ratio=4.0, kernel_size=7):
        super().__init__()
        self.attn = nn.MultiheadAttention(dim, num_heads, batch_first=True, bias=False)
        self.norm1 = nn.LayerNorm(dim)
        
        padding = kernel_size // 2
        self.conv = nn.Sequential(
            nn.Conv2d(dim, dim, kernel_size, padding=padding, groups=dim, bias=False),
            nn.BatchNorm2d(dim),
            nn.GELU()
        ) # Lớp convolution giữ nguyên kích thước
        self.norm2 = nn.LayerNorm(dim)
        
        mlp_dim = int(dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(dim, mlp_dim),
            nn.GELU(),
            nn.Linear(mlp_dim, dim)
        )
        self.norm3 = nn.LayerNorm(dim)
        self._init_weight()
    def _init_weight(self):
        for name, param in self.attn.named_parameters():
            if 'weight' in name:
                nn.init.xavier_uniform_(param)
        
        for m in self.conv.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
        
        for m in self.mlp.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
        
        for m in [self.norm1, self.norm2, self.norm3]:
            nn.init.constant_(m.weight, 1)
            nn.init.constant_(m.bias, 0)
        
    def forward(self, x):
        B, D, H, W = x.shape
        
        x_flat = x.flatten(2).transpose(1, 2) 
        attn_out, attn_weight = self.attn(x_flat, x_flat, x_flat)
        self.attn_weight = attn_weight
        x_flat = x_flat + attn_out
        x_flat = self.norm1(x_flat)
        
        x = x_flat.transpose(1, 2).reshape(B, D, H, W)
        
        conv_out = self.conv(x)
        x = x + conv_out
        x_flat = self.norm2(x.flatten(2).transpose(1, 2))
        
        mlp_out = self.mlp(x_flat)
        x_flat = x_flat + mlp_out
        x_flat = self.norm3(x_flat)
        
        x = x_flat.transpose(1, 2).reshape(B, D, H, W)
        return x

class ConformerClassifier(nn.Module):
    def __init__(self, in_channels=2, num_classes=3, embed_dim=64, depth=4, num_heads=4):
        super().__init__()
        self.patch_embed = nn.Sequential(
            nn.Conv2d(in_channels, embed_dim, kernel_size=4, stride=4, bias=False),
            nn.BatchNorm2d(embed_dim),
            nn.GELU()
        )
        
        self.conformer_blocks = nn.ModuleList([
            ConformerBlock(embed_dim, num_heads, mlp_ratio=4.0, kernel_size=7)
            for _ in range(depth)
        ])
        
        self.norm = nn.LayerNorm(embed_dim)
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.head = nn.Linear(embed_dim, num_classes, bias=False)
        print(f"Tong luong tham so: {self.count_parameters()}")
        self._init_weights()
        
    def _init_weights(self):
        for m in self.patch_embed.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
        
        nn.init.constant_(self.norm.weight, 1)
        nn.init.constant_(self.norm.bias, 0)
        
        nn.init.normal_(self.head.weight, mean=0.0, std=0.01)
    def forward(self, x):
        # x: [batch_size, channels, 64, 64]
        # Patch embedding: [batch_size, channels, 64, 64] -> [batch_size, embed_dim, 16, 16]
        x = self.patch_embed(x)
        # Conformer blocks
        attn_weights = []
        for block in self.conformer_blocks:
            x = block(x)
            attn_weights.append(block.attn_weight)
        x = self.pool(x)
        x = x.flatten(1)  # [batch_size, embed_dim]
        x = self.norm(x)
        x = self.head(x)  # [batch_size, num_classes]
        return x, attn_weights
    
    def count_parameters(self):
        """Đếm tổng số parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
def main():
    model = ConformerClassifier()
    # writer = SummaryWriter("Test/123")
    
# Example usage
if __name__ == "__main__":
    # testSpeed()
    main()