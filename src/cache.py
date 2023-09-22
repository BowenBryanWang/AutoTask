import json, pickle, os, time

def persist_to_file(file_name, use_cache=True):
    def decorator(original_func):
        try:
            cache = pickle.load(open(file_name, 'rb'))
        except (IOError, ValueError):
            cache = {}

        def new_func(*argv, **args):
            arg_s = json.dumps({
                'argv': argv, 
                'args': args
            })
            cache_used = True
            if use_cache and arg_s in cache:
                res = cache[arg_s]
                if res is None or len(res) == 0:
                    del cache[arg_s]
            if arg_s not in cache or not use_cache:
                cache[arg_s] = original_func(*argv, **args)
                cache_used = False
                pickle.dump(cache, open(file_name, 'wb'))
            
            if 'prompt' in args:
                store_path = os.path.join(os.path.dirname(__file__), 'gpt_res')
                if not os.path.exists(store_path):
                    os.makedirs(store_path)
                
                store_path = os.path.join(store_path, f"{int(time.time() * 1000)}{'cache' if cache_used else ''}.txt")
                with open(store_path, 'w') as f:
                    f.write('\n'.join([f'{x["role"]}:\n{x["content"]}\n' for x in args['prompt']]))
                    f.write('\n')
                    f.write('===response===\n')
                    f.write(cache[arg_s])
            return cache[arg_s]
        return new_func
    return decorator