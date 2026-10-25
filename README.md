# someip-contract

SOME/IP 服务接口合同检查器。输入服务、方法、事件和字段的 JSON 描述，检查 ID 碰撞、版本号、范围和方法/事件的重复定义，帮助在 ECU 集成前发现接口不兼容。

## 痛点

SOME/IP 同时涉及序列化、RPC、发布订阅和 Service Discovery；小的 ID 或版本差异会导致跨 ECU 互操作失败，而错误常要到网络联调才出现。本工具不发送报文，只检查可版本化的接口合同。

## 使用

    python someiplint.py examples/service.json

## 许可证

MIT
