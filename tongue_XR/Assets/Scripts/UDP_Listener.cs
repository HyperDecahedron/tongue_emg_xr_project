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

    public event Action<string> OnClassReceived; // event for updates

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

                    Debug.Log("UDP: " + currentClass);

                    OnClassReceived?.Invoke(currentClass); // Raise event
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

    void OnApplicationQuit()
    {
        receiveThread?.Abort();
        udpClient?.Close();
    }
}
