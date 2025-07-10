using System.Collections.Concurrent;
using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UDP_Listener : MonoBehaviour
{
    private UdpClient udpClient;
    private Thread receiveThread;

    public string currentClass = "n";
    public int[] currentPressure = new int[3];

    // Define a struct to hold both class and pressure data
    public struct UdpData
    {
        public string Class;
        public int[] Pressure;

        public UdpData(string classLabel, int[] pressure)
        {
            Class = classLabel;
            Pressure = pressure;
        }
    }

    // Event that includes both class and pressure
    public event Action<UdpData> OnDataReceived;

    // Thread-safe queue to send data to Unity main thread
    private ConcurrentQueue<UdpData> mainThreadQueue = new ConcurrentQueue<UdpData>();

    void Start()
    {
        udpClient = new UdpClient(5052);
        receiveThread = new Thread(ReceiveData);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveData()
    {
        IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 5052);
        while (true)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                string message = Encoding.ASCII.GetString(data).Trim().ToLower();

                string[] parts = message.Split(',');

                if (parts.Length == 4)
                {
                    string pos = parts[0];
                    int p0 = int.Parse(parts[1]);
                    int p1 = int.Parse(parts[2]);
                    int p2 = int.Parse(parts[3]);

                    lock (this)
                    {
                        currentClass = pos;
                        currentPressure[0] = p0;
                        currentPressure[1] = p1;
                        currentPressure[2] = p2;
                    }

                    // Create a new UdpData object and enqueue it
                    UdpData udpData = new UdpData(pos, new int[] { p0, p1, p2 });
                    mainThreadQueue.Enqueue(udpData);
                }
                else
                {
                    Debug.LogWarning("Invalid UDP message format: " + message);
                }
            }
            catch (Exception ex)
            {
                Debug.Log("UDP receive error: " + ex.Message);
            }
        }
    }

    void Update()
    {
        while (mainThreadQueue.TryDequeue(out UdpData data))
        {
            OnDataReceived?.Invoke(data); // Trigger event with full data
        }
    }

    void OnApplicationQuit()
    {
        receiveThread?.Abort();
        udpClient?.Close();
    }
}
