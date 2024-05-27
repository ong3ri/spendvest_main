import redis
import time
import json

redis_client = redis.Redis(host="localhost", port=6379, db=10)
print(f"testing redis connection, {redis_client.ping()}")

class Session():
    def __init__(
            self,
            uid,
            waid,
            name,
            user_flow,
            current_menu_code=None,
            answer_payload=None,
            is_slot_filling=False,
            current_slot_count=0,
            slot_quiz_count=0,
            current_slot_handler=None
    ):
        self.uid = uid
        self.waid = waid
        self.name = name
        self.current_menu_code = current_menu_code
        self.answer_payload = answer_payload if answer_payload is not None else []
        self.slot_filling = is_slot_filling
        self.user_flow = user_flow
        self.current_slot_count = current_slot_count
        self.slot_quiz_count = slot_quiz_count
        self.current_slot_handler = current_slot_handler
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def save(self):
        session_data = {
            'uid': self.uid,
            'waid': self.waid,
            'name': self.name,
            'current_menu_code': self.current_menu_code,
            'answer_payload': self.answer_payload,  # Serialize the list
            'slot_filling': self.slot_filling,  # Serialize the boolean
            'user_flow': self.user_flow,
            'current_slot_count': self.current_slot_count,
            'slot_quiz_count': self.slot_quiz_count,
            'current_slot_handler': self.current_slot_handler,
            'created_at': self.created_at,
            'updated_at': time.time()
        }
        redis_client.sadd("user:set", self.waid)
        redis_client.hmset(f"session:{self.waid}", session_data)
    
    @staticmethod
    def get_session(waid):
        if redis_client.sismember("user:set", waid):
            session_data = redis_client.hgetall(f"session:{waid}")
            if session_data:
                return session_data
            return None
        return None
    
    def delete(self):
        if redis_client.sismember("user:set", self.waid):
            redis_client.srem("user:set", self.waid)
            return redis_client.delete(f"session:{self.waid}")
        return None
    
    def save_current_input(self, curr_input):
        self.answer_payload.append(curr_input)
        self.updated_at = time.time()
        self.save()

    # utility functions
    @staticmethod
    def is_first_time_contact(waid):
        return redis_client.sismember('user:set', waid)
    
    @staticmethod
    def is_slot_filling(waid):
        user_session = Session.get_session(waid)
        if user_session[b'slot_filling'].decode('utf-8') == '0':
            return False 
        else:
            return True
        
    @staticmethod
    def set_slot_filling_on(waid):
        user_session = Session.get_session(waid)
        print(f"setting slot filling on, session:{user_session}")
        return redis_client.hset(f"session:{waid}", "slot_filling", 1)
    
    @staticmethod
    def load_handler(waid, handler, menu_code, current_slot_count, quiz_count):
        return redis_client.hmset(f"session:{waid}", {"current_slot_handler":handler, 
                                                      "current_menu_code":menu_code, 
                                                      "current_slot_count":current_slot_count,
                                                      "slot_quiz_count":quiz_count})
    
    @staticmethod
    def fetch_slot_details(waid):
        user_session = Session.get_session(waid)
        
        return {
            "menu_code":user_session[b'current_menu_code'].decode('utf-8'),
            "slot_count":user_session[b'current_slot_count'].decode('utf-8'),
            "quiz_count":user_session[b'slot_quiz_count'].decode('utf-8')
        }
    
    @staticmethod
    def return_current_slot_quiz(waid, quiz_payload):
        print(f"recieved slot quiz_pack is {quiz_payload}")
        current_slot_count = redis_client.hget(f"session:{waid}", "current_slot_count").decode('utf-8')
        print(f"current_slot_count is {current_slot_count}")
        return quiz_payload[current_slot_count]
    
    @staticmethod
    def step_slotting(waid, quiz_payload):
        current_slot_count = redis_client.hget(f"session:{waid}", "current_slot_count").decode('utf-8')
        quiz_length = len(quiz_payload)
        quiz_index_length = quiz_length - 1
        count_ = int(current_slot_count) 
        print(f"stepping from count_ : {count_}")

        if count_ == quiz_index_length :
            print(f"questions over, not stepping, should be resetting")
            pass 
        elif count_ < quiz_index_length:
            count_ += 1
            redis_client.hset(f"session:{waid}", "current_slot_count", count_)
        
         
    
    @staticmethod
    def load_ans_payload(waid):
        ans_payload = redis_client.hget(f"session:{waid}", "answer_payload")
        return ans_payload.decode('utf-8')

    @staticmethod
    def save_answer(waid, curr_count_, ans):
        current_ans_payload = Session.load_ans_payload(waid)
        curr_count = int(curr_count_) - 1
        # new_entry = {curr_count: ans}
        new_entry = ans
        new_payload = ''

        if current_ans_payload == '[]':
            print("Empty answer payload")
            new_payload = json.dumps([new_entry])  # Create a list with the new entry
        else:
            print(f"Not empty answer payload : {current_ans_payload}")
            existing_payload = json.loads(current_ans_payload)
            if len(existing_payload) >= 2:
                existing_payload.append(new_entry)
                new_payload = json.dumps(existing_payload)
                 
            else:
            
                existing_payload.append(new_entry)
                new_payload = json.dumps(existing_payload)

                

        # Save the updated payload back to the session
        session = Session.get_session(waid)
        print(f"fetched session is : {session}")
        if session:
            redis_client.hmset(f"session:{waid}", {
                "answer_payload":new_payload,
                "updated_at":time.time()
            })
            
    @staticmethod
    def clear_answer_slot(waid):
        redis_client.hset(f"session:{waid}", "answer_payload", '[]')

    @staticmethod
    def complete_reg_slotting(waid):
        print(f"calling complete registeration function")
        current_ans_payload = Session.load_ans_payload(waid)
        json_loaded = json.loads(current_ans_payload)
        print(f"current answer payload is : {json_loaded}, and type is {type(json_loaded)}")
        payload_length = len(json_loaded)
        print(f"payload length is  {payload_length}")
         
        if payload_length == 2:
            if json_loaded[0] == json_loaded[1]:
                print(f"answer is the same")
                Session.clear_answer_slot(waid)
                return True
            else:
                print(f"answers not the same")
                return False 
        
        if payload_length == 1:
            print(f"current answer is : {json_loaded[0]}")
            return False 

         


    @staticmethod
    def complete_sm_slotting(waid):
        print(f"calling complete send_money function")
        current_ans_payload = Session.load_ans_payload(waid)
        json_loaded = json.loads(current_ans_payload)
        print(f"current answer payload is : {json_loaded}, and type is {type(json_loaded)}")
        payload_length = len(json_loaded)
        print(f"payload length is  {payload_length}")
         
        
        if payload_length == 1:
            print(f"current answer is : {json_loaded[0]}")
            return False
        
        if payload_length == 3:
            print(f"payload_length : {payload_length}")
            if json_loaded[0] == json_loaded[1]:
                print(f"answer is the same")
                Session.clear_answer_slot(waid)
                return True
            else:
                print(f"answers not the same")
                return False
