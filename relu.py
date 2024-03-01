import torch
import triton
import triton.language as tl
from .libentry import libentry

@libentry()
@triton.autotune(configs=[
    triton.Config({"M_BLOCK_SIZE": 256}, num_warps=2, num_stages=4),
    triton.Config({"M_BLOCK_SIZE": 256}, num_warps=2, num_stages=5),
    triton.Config({"M_BLOCK_SIZE": 512}, num_warps=2, num_stages=4),
    triton.Config({"M_BLOCK_SIZE": 512}, num_warps=2, num_stages=5),
    triton.Config({"M_BLOCK_SIZE": 1024}, num_warps=4, num_stages=4),
    triton.Config({"M_BLOCK_SIZE": 1024}, num_warps=4, num_stages=5),
    triton.Config({"M_BLOCK_SIZE": 2048}, num_warps=4, num_stages=4),
    triton.Config({"M_BLOCK_SIZE": 2048}, num_warps=4, num_stages=5),
    ],
    key=["M"]
)
@triton.jit
def relu_kernel(
    X,
    Y,
    M,
    M_BLOCK_SIZE: tl.constexpr,
):
    pid = tl.program_id(0) * M_BLOCK_SIZE
    Y_ptrs = tl.make_block_ptr(
        Y,
        shape=(M, ),
        strides=(1, ),
        offsets=(pid, ),
        block_shape=(M_BLOCK_SIZE, ),
        order=(0, )
    )
    X_ptrs = tl.make_block_ptr(
        X,
        shape=(M, ),
        strides=(1, ),
        offsets=(pid, ),
        block_shape=(M_BLOCK_SIZE, ),
        order=(0, )
    )
    X_val = tl.load(X_ptrs)
    Y_val = tl.where(X_val > 0, X_val, 0)
    tl.store(Y_ptrs, Y_val)


def relu(A):
    print("FLAG RELU")
    A = A.contiguous()
    M = A.numel()
    O = torch.empty_like(A)
    grid_fn = lambda meta: (triton.cdiv(M, meta["M_BLOCK_SIZE"]), )
    relu_kernel[grid_fn](A, O, M)
    return O