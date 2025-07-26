import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消

@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 进度百分比 0-100
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    error_message: Optional[str] = None
    result_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于JSON序列化"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

class TaskManager:
    """异步任务管理器
    
    负责管理数据分析任务的生命周期，包括：
    - 任务创建和调度
    - 进度跟踪和状态更新
    - 结果存储和检索
    - 错误处理和重试机制
    """
    
    def __init__(self, max_concurrent_tasks: int = 3):
        self.tasks: Dict[str, TaskInfo] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self._task_handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器
        
        Args:
            task_type: 任务类型标识
            handler: 异步处理函数，签名为 async def handler(task_info, **kwargs)
        """
        self._task_handlers[task_type] = handler
    
    async def create_task(self, task_type: str, **kwargs) -> str:
        """创建新任务
        
        Args:
            task_type: 任务类型
            **kwargs: 任务参数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=kwargs
        )
        
        async with self._lock:
            self.tasks[task_id] = task_info
        
        # 尝试立即执行任务
        await self._try_execute_pending_tasks()
        
        return task_id
    
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        task_info = self.tasks.get(task_id)
        return task_info.status if task_info else None
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Returns:
            是否成功取消
        """
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task_info = self.tasks[task_id]
            
            if task_info.status == TaskStatus.RUNNING:
                # 取消正在运行的任务
                if task_id in self.running_tasks:
                    self.running_tasks[task_id].cancel()
                    del self.running_tasks[task_id]
            
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()
            
        return True
    
    async def update_progress(self, task_id: str, progress: float, 
                            current_step: str = "", completed_steps: Optional[int] = None):
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            current_step: 当前步骤描述
            completed_steps: 已完成步骤数
        """
        if task_id not in self.tasks:
            return
        
        task_info = self.tasks[task_id]
        task_info.progress = max(0, min(100, progress))
        if current_step:
            task_info.current_step = current_step
        if completed_steps is not None:
            task_info.completed_steps = completed_steps
    
    async def _try_execute_pending_tasks(self):
        """尝试执行等待中的任务"""
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return
        
        # 查找等待执行的任务
        pending_tasks = [
            task_info for task_info in self.tasks.values()
            if task_info.status == TaskStatus.PENDING
        ]
        
        # 按创建时间排序
        pending_tasks.sort(key=lambda t: t.created_at)
        
        for task_info in pending_tasks:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                break
            
            await self._execute_task(task_info)
    
    async def _execute_task(self, task_info: TaskInfo):
        """执行单个任务"""
        if task_info.task_type not in self._task_handlers:
            task_info.status = TaskStatus.FAILED
            task_info.error_message = f"未找到任务类型 '{task_info.task_type}' 的处理器"
            task_info.completed_at = datetime.now()
            return
        
        # 创建异步任务
        async_task = asyncio.create_task(
            self._run_task_handler(task_info)
        )
        
        self.running_tasks[task_info.task_id] = async_task
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.now()
    
    async def _run_task_handler(self, task_info: TaskInfo):
        """运行任务处理器"""
        try:
            handler = self._task_handlers[task_info.task_type]
            metadata = task_info.metadata or {}
            result = await handler(task_info, **metadata)
            
            # 任务成功完成
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now()
            task_info.progress = 100.0
            
            if isinstance(result, str):  # 结果路径
                task_info.result_path = result
            
        except asyncio.CancelledError:
            # 任务被取消
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()
            
        except Exception as e:
            # 任务执行失败
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            task_info.completed_at = datetime.now()
            
        finally:
            # 清理运行中的任务记录
            if task_info.task_id in self.running_tasks:
                del self.running_tasks[task_info.task_id]
            
            # 尝试执行下一个等待的任务
            await self._try_execute_pending_tasks()
    
    async def get_all_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[TaskInfo]:
        """获取所有任务信息
        
        Args:
            status_filter: 状态过滤器，None表示获取所有状态的任务
            
        Returns:
            任务信息列表
        """
        tasks = list(self.tasks.values())
        
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        # 按创建时间倒序排列
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks
    
    async def cleanup_completed_tasks(self, keep_recent: int = 100):
        """清理已完成的任务
        
        Args:
            keep_recent: 保留最近的任务数量
        """
        completed_tasks = [
            task_info for task_info in self.tasks.values()
            if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        if len(completed_tasks) <= keep_recent:
            return
        
        # 按完成时间排序，删除最旧的任务
        completed_tasks.sort(key=lambda t: t.completed_at or t.created_at)
        tasks_to_remove = completed_tasks[:-keep_recent]
        
        async with self._lock:
            for task_info in tasks_to_remove:
                if task_info.task_id in self.tasks:
                    del self.tasks[task_info.task_id]

# 全局任务管理器实例
task_manager = TaskManager()