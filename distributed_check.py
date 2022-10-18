import os
import torch
import argparse

import torch.distributed as dist
import torchvision


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--local_rank', type=int)
    parser.add_argument('--gpu-id', type=int, default=None)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    distributed = False

    if 'WORLD_SIZE' in os.environ and int(os.environ['WORLD_SIZE']) > 1:
        distributed = True
        print('This is {} rank of {} process'.format(
            os.environ['RANK'], os.environ['WORLD_SIZE']))

    nprocs_per_node = os.environ['LOCAL_WORLD_SIZE'] if distributed else -1

    model = torchvision.models.resnet18(pretrained=False)

    if not distributed:
        # 1. cpu
        # 2. single gpu(this), single node, single process
        # 3. multi gpu(this), single node, single process : DP
        if torch.cuda.is_available():
            # get gpu count
            if args.gpu_id is None:
                # multi gpu
                print('This mode uses multi gpu and single process.. use DataParallel..')
            else:
                # single gpu
                print('This mode uses single gpu and single process with cuda..')
        elif torch.backends.mps.is_available():
            # single gpu
            print('This mode uses single gpu and single process with mps..')
        else:
            print('This mode uses cpu..')
    else:
        # 4. single gpu(this), multi node, multi process : DDP
        # 5. multi gpu(this), single node, multi process : DDP
        # 6. multi gpu(this), multi node, multi process : DDP
        if torch.cuda.is_available():
            if args.gpu_id is None and nprocs_per_node > 1:
                print('This mode is multi gpu and multi process with cuda..')
            else:
                print('This mode is single gpu and multi process with cuda..')

            print(
                'Initalization...{}/{}'.format(os.environ['RANK'], int(os.environ['WORLD_SIZE'])-1))

            dist.init_process_group(backend='nccl', init_method='env://', world_size=int(
                os.environ['WORLD_SIZE']), rank=int(os.environ['RANK']))

            if torch.distributed.is_initialized():
                print('Distribution is initalized.')
            else:
                print('Distirbution is not initalized.')

            ddp_model = torch.nn.parallel.DistributedDataParallel(
                model, device_ids=args.local_rank, output_device=args.local_rank)
            print('Get the DDP model.')
        else:
            print(
                'This mode is not supported because distribution operates with cuda gpu..')


if __name__ == "__main__":
    main()